"""Opt-in final-package cloth diagnostics for build, packaging and installation."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))
from project_paths import resolve_project

SCHEMA = 1
RUNTIME_SOURCES = [
    'cloth_simulator/pipeline.py', 'cloth_simulator/run.py', 'cloth_simulator/solver.py',
    'cloth_simulator/viewer.html', 'cloth_simulator/README.md', 'project_paths.py',
    'cloth_compiler/cloth_payload.py', 'cloth_compiler/validation.py',
    'cloth_compiler/NativeClothProbe.cs', 'cloth_compiler/NativeClothProbe.csproj',
    'asset_helpers/previewer/baker/__init__.py',
    'asset_helpers/previewer/baker/skeleton.py', 'asset_helpers/previewer/baker/animation.py',
]
SETTINGS = {'substeps', 'iterations', 'damping', 'stretch', 'shear', 'bend', 'anchor',
            'gravity', 'thickness', 'penetration_tolerance', 'strain_tolerance', 'warmup', 'no_dummy'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project_file(root, relative):
    if not isinstance(relative, str):
        raise ValueError('diagnostic paths must be relative strings')
    path = (root/relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('missing diagnostic input or path outside mod: '+relative)
    return path


def normalize(root, config):
    spec = config.get('cloth_diagnostics')
    if spec is None or (isinstance(spec, dict) and spec.get('enabled') is False):
        return None
    if not isinstance(spec, dict) or spec.get('enabled') is not True:
        raise ValueError('cloth_diagnostics.enabled must be boolean')
    if set(spec)-{'enabled', 'mode', 'probe', 'targets'}:
        raise ValueError('unknown cloth_diagnostics settings')
    if spec.get('mode', 'report') not in ('report', 'strict'):
        raise ValueError('cloth_diagnostics.mode must be report or strict')
    probe = project_file(root, spec['probe'])
    package = project_file(root, config['package'])
    if not package.is_relative_to((root/'module'/config['id']).resolve()):
        raise ValueError('diagnostic TPAC must be inside this mod module')
    targets = spec.get('targets')
    if not isinstance(targets, list) or not targets:
        raise ValueError('diagnostics requires nonempty targets')
    inputs = {package, probe}
    inputs.update(p for p in probe.parent.iterdir() if p.is_file() and
                  (p.suffix.lower() == '.dll' or p.name.endswith(('.runtimeconfig.json', '.deps.json'))))
    names = set()
    for target in targets:
        if set(target)-{'metamesh', 'skeleton', 'capsules', 'body', 'lods', 'meshes', 'motions', 'settings'}:
            raise ValueError('unknown diagnostic target fields')
        if not isinstance(target.get('metamesh'), str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', target['metamesh']) or target['metamesh'] in names:
            raise ValueError('targets require unique metamesh names')
        names.add(target['metamesh'])
        inputs.add(project_file(root, target['skeleton']))
        inputs.add(project_file(root, target['capsules']))
        if not isinstance(target.get('body'), str) or not target['body']:
            raise ValueError('target body required')
        lods = target.get('lods', [0])
        if not isinstance(lods, list) or not lods or any(type(v) is not int or v < 0 for v in lods):
            raise ValueError('lods must be nonempty nonnegative integers')
        meshes = target.get('meshes')
        if meshes is not None and (not isinstance(meshes, list) or not meshes or any(not isinstance(v, str) or not v for v in meshes)):
            raise ValueError('meshes must be a nonempty list of exact names, or omitted')
        if set(target.get('settings', {}))-SETTINGS:
            raise ValueError('unknown solver diagnostic settings')
        motions = target.get('motions')
        if not isinstance(motions, list) or not motions:
            raise ValueError('each target needs motions')
        labels = set()
        for motion in motions:
            if set(motion)-{'name', 'path', 'fps', 'start', 'end'}:
                raise ValueError('unknown motion fields')
            if not isinstance(motion.get('name'), str) or not motion['name'] or motion['name'] in labels:
                raise ValueError('motions require unique names')
            labels.add(motion['name'])
            if type(motion.get('fps')) not in (int, float) or not 0 < motion['fps'] < float('inf'):
                raise ValueError('explicit finite positive animation fps required')
            inputs.add(project_file(root, motion['path']))
    return spec, package, probe, inputs


def fingerprint(root, spec, inputs):
    import numpy
    inventory = {'mod/'+p.relative_to(root).as_posix(): sha(p) for p in sorted(inputs)}
    for relative in RUNTIME_SOURCES:
        inventory['workspace_tools/'+relative] = sha(TOOLS/relative)
    inventory['mod/mod.json'] = sha(root/'mod.json')
    canonical = json.dumps(dict(schema=SCHEMA, config=spec, inputs=inventory,
                    python=sys.version, numpy=numpy.__version__), sort_keys=True, allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest(), inventory


def aggregate(results):
    statuses = {r['status'] for r in results}
    if 'error' in statuses or not statuses:
        return 'error'
    if 'incomplete' in statuses:
        return 'incomplete'
    return 'needs_review' if 'needs_review' in statuses else 'within_thresholds'


def valid_cached(root, report, stamp):
    if not isinstance(report, dict) or not isinstance(report.get('results'), list):
        return False
    if report.get('schema') != SCHEMA or report.get('fingerprint') != stamp:
        return False
    if report.get('status') == 'error' or report.get('status') != aggregate(report.get('results', [])):
        return False
    for result in report['results']:
        if not isinstance(result, dict) or not isinstance(result.get('artifacts', {}), dict):
            return False
        for relative, expected in result.get('artifacts', {}).items():
            try:
                path = project_file(root, relative)
                if not path.is_relative_to((root/'build/cloth_simulator').resolve()) or sha(path) != expected:
                    return False
            except ValueError:
                return False
        if result['status'] in ('within_thresholds', 'needs_review') and not result.get('artifacts'):
            return False
    return True


def write_summary(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique temporary file makes overlapping independent runs safe to preserve.
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, suffix='.tmp',
                                     encoding='utf-8', delete=False) as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        temp = Path(stream.name)
    temp.replace(path)


def run_pipeline(root, config=None, force=False):
    root = Path(root).resolve()
    config = config or json.loads((root/'mod.json').read_text(encoding='utf-8-sig'))
    validated = normalize(root, config)
    if validated is None:
        return None
    spec, package, probe, inputs = validated
    stamp, inventory = fingerprint(root, spec, inputs)
    summary = root/'reports/cloth_diagnostics.json'
    if not force and summary.is_file():
        try:
            cached = json.loads(summary.read_text(encoding='utf-8'))
            if valid_cached(root, cached, stamp):
                print('Cloth diagnostics: reused '+cached['status'])
                return cached
        except (ValueError, KeyError, TypeError):
            pass
    cache = root/'build/cloth_simulator'
    cache.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=stamp[:12]+'-', dir=cache))
    report = dict(schema=SCHEMA, mod=config['id'], fingerprint=stamp,
                  generated_at_utc=datetime.now(timezone.utc).isoformat(), inputs=inventory,
                  config=spec, package_sha256=sha(package), package_relative_path=package.relative_to(root).as_posix(), game_solver_used=False,
                  game_verified=False, coverage='configured targets, meshes, LODs and motions only',
                  results=[], run_directory=run_dir.relative_to(root).as_posix())
    from cloth_simulator.run import extract
    for ti, target in enumerate(spec['targets']):
        target_dir = run_dir/f'target_{ti:02d}'
        try:
            extract(SimpleNamespace(output=target_dir/'input', probe=probe, tpac=package,
                                    metamesh=target['metamesh'], allow_empty=True))
            metadata = json.loads((target_dir/'input/package.json').read_text(encoding='utf-8'))['metadata']
            mm = next(m for m in metadata if m['Name'] == target['metamesh'])
            if mm.get('ClothMetamesh') not in (None, '', '00000000-0000-0000-0000-000000000000'):
                report['results'].append(dict(metamesh=target['metamesh'], status='incomplete', reason='mapped cloth is not supported by this direct-cloth diagnostic'))
                continue
            selected = []
            for mesh_path in sorted((target_dir/'input').glob('*.mesh.json')):
                mesh = json.loads(mesh_path.read_text(encoding='utf-8'))
                if mesh['lod'] in target.get('lods', [0]) and (not target.get('meshes') or mesh['name'] in target['meshes']):
                    selected.append((mesh_path, mesh))
            matched_names = {m['name'] for _, m in selected}
            missing = set(target.get('meshes', []))-matched_names
            missing_lods = set(target.get('lods', [0]))-{m['lod'] for _, m in selected}
            if not selected or missing or missing_lods:
                report['results'].append(dict(metamesh=target['metamesh'], status='incomplete',
                    reason='requested cloth mesh/LOD selection missing', missing_meshes=sorted(missing), missing_lods=sorted(missing_lods)))
            for mesh_path, mesh in selected:
                payload = mesh_path.with_name(mesh_path.name.removesuffix('.mesh.json')+'.bin')
                mesh_meta = next(m for m in mm['meshes'] if m['Guid'] == mesh['guid'])
                for mi, motion in enumerate(target['motions']):
                    case = target_dir/f'case_{len(report["results"]):04d}'
                    args = [sys.executable, '-B', '-X', 'utf8', str(HERE/'run.py'), 'simulate',
                            '--payload', str(payload), '--mesh', str(mesh_path), '--skeleton', str(project_file(root, target['skeleton'])),
                            '--animation', str(project_file(root, motion['path'])), '--capsules', str(project_file(root, target['capsules'])),
                            '--body', target['body'], '--fps', str(motion['fps']), '--multiplier', str(mesh_meta['UnknownFloat1']), '--output', str(case)]
                    for key in ('start', 'end'):
                        if key in motion:
                            args.extend(['--'+key, str(motion[key])])
                    for key, value in target.get('settings', {}).items():
                        if key == 'no_dummy':
                            if type(value) is not bool:
                                raise ValueError('no_dummy must be boolean')
                            if value:
                                args.append('--no-dummy')
                        else:
                            args.extend(['--'+key.replace('_', '-'), str(value)])
                    print(f'Cloth diagnostic: {mesh["name"]} / {motion["name"]}', flush=True)
                    completed = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    (target_dir/f'{case.name}.log').write_text(completed.stdout+'\n'+completed.stderr, encoding='utf-8')
                    result = dict(metamesh=target['metamesh'], mesh=mesh['name'], lod=mesh['lod'], motion=motion['name'])
                    if not (case/'report.json').is_file() or completed.returncode not in (0, 1, 2):
                        result.update(status='error', reason=completed.stderr[-2000:] or 'simulator produced no report')
                    else:
                        detail = json.loads((case/'report.json').read_text(encoding='utf-8'))
                        expected = {'within_thresholds':0, 'needs_review':1, 'incomplete':2}
                        if expected.get(detail['status']) != completed.returncode:
                            raise ValueError('simulator status and exit code disagree')
                        artifacts = {p.relative_to(root).as_posix():sha(p) for p in case.iterdir() if p.is_file()}
                        result.update(status=detail['status'], frames=detail['frames'], maxima=detail['maxima'],
                            artifacts=artifacts, report=(case/'report.json').relative_to(root).as_posix(),
                            archive_directory='reports/cloth_diagnostics/'+run_dir.name+f'/case_{len(report["results"]):04d}')
                    report['results'].append(result)
        except (ValueError, KeyError, OSError, StopIteration, subprocess.CalledProcessError) as error:
            report['results'].append(dict(metamesh=target['metamesh'], status='error', reason=str(error)))
    # An input changed mid-run: the result must never be accepted for packaging.
    new_stamp, _ = fingerprint(root, spec, inputs)
    if new_stamp != stamp:
        report['results'].append(dict(status='error', reason='diagnostic inputs changed during simulation'))
    report['status'] = aggregate(report['results'])
    write_summary(summary, report)
    print('Cloth diagnostics: '+report['status']+'; '+str(summary))
    return report


def ensure_diagnostics(root, config):
    report = run_pipeline(root, config)
    if report is None:
        return None
    if report['status'] == 'error':
        raise ValueError('cloth diagnostic failed; see reports/cloth_diagnostics.json')
    if config['cloth_diagnostics'].get('mode', 'report') == 'strict' and report['status'] != 'within_thresholds':
        raise ValueError('strict cloth diagnostic requires within_thresholds; got '+report['status'])
    if report['status'] != 'within_thresholds':
        print('Cloth diagnostic notice: '+report['status']+' (report mode); game verification remains separate.')
    return report


def delivery_files(root, report):
    """Ship reports/PNGs, input configuration and runnable shared sources in Source ZIP."""
    if report is None:
        return [], []
    local = [(root/'reports/cloth_diagnostics.json', 'reports/cloth_diagnostics.json'),
             (root/'mod.json', 'mod.json')]
    for relative in report['inputs']:
        if relative.startswith('mod/'):
            name = relative[4:]
            if name != report['package_relative_path'] and (root/name).parent != (root/report['config']['probe']).parent:
                local.append((project_file(root, name), name))
    for result in report['results']:
        for relative in result.get('artifacts', {}):
            path = project_file(root, relative)
            if path.name in ('report.json', 'worst_frame.png', 'worst_stretch.png'):
                local.append((path, result['archive_directory']+'/'+path.name))
    shared = [(TOOLS/relative, 'workspace_tools/'+relative) for relative in RUNTIME_SOURCES]
    return local, shared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument('--mod')
    which.add_argument('--project', type=Path, help='explicit mod root, including an extracted Source archive')
    parser.add_argument('--force', action='store_true', help='create another retained run instead of reusing cache')
    args = parser.parse_args()
    try:
        root = args.project.resolve() if args.project else resolve_project(TOOLS.parent, args.mod)
        report = run_pipeline(root, force=args.force)
        if report is None:
            print('Cloth diagnostics disabled; no files written.')
            return 0
        return {'within_thresholds':0, 'needs_review':1, 'incomplete':2, 'error':2}[report['status']]
    except (ValueError, KeyError, TypeError, OSError) as error:
        print('Cloth pipeline error: '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
