"""Offline native-data cloth diagnostics. Inputs are read-only; outputs are explicit."""
from pathlib import Path
import argparse
from dataclasses import asdict
import hashlib
import html
import json
import subprocess
import struct
import sys
import xml.etree.ElementTree as ET
import numpy as np

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path[:0] = [str(TOOLS), str(TOOLS/'asset_helpers/previewer')]
from cloth_compiler.cloth_payload import read, decode_positions
from cloth_compiler.validation import check_structure
from solver import Settings, Simulator


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capsule_tracks(xml_path, body_name, rig, matrices):
    """Read this workspace's authored row-major capsule frames, x axis = length.

    This convention has not been checked against all native body resources.
    Unknown/missing bones and malformed weights are rejected, never guessed.
    """
    bodies = ET.parse(xml_path).getroot().findall('body')
    matches = [b for b in bodies if b.get('name') == body_name]
    if len(matches) != 1:
        raise ValueError('body name must select exactly one collision body')
    definitions = matches[0].findall('./capsules/capsule')
    result = np.zeros((len(matrices), len(definitions), 2, 4))
    names = {name: i for i, name in enumerate(rig['names'])}
    tapered = False
    for ci, cap in enumerate(definitions):
        frame = np.fromstring(cap.get('frame', ''), sep=',').reshape(4, 4)
        origin = np.fromstring(cap.get('origin', '0,0,0'), sep=',')
        length = float(cap.attrib['length'])
        if origin.shape != (3,) or not np.isfinite(origin).all() or not np.isfinite(length) or length < 0 or not np.isfinite(frame).all():
            raise ValueError('invalid capsule frame/origin/length')
        points = cap.findall('./points/point')
        if len(points) != 2:
            raise ValueError('capsule requires two points')
        for pi, point in enumerate(points):
            rest = np.r_[frame[3, :3]+origin+pi*length*frame[0, :3], 1.]
            influences = point.findall('./bones/bone')
            weights = [float(b.attrib['weight']) for b in influences]
            if not 1 <= len(weights) <= 2 or min(weights) < 0 or abs(sum(weights)-1) > 1e-5:
                raise ValueError('capsule point must have 1-2 bones with weights summing to 1')
            for bone, weight in zip(influences, weights):
                if bone.attrib['name'] not in names:
                    raise ValueError('unknown collision bone: '+bone.attrib['name'])
                result[:, ci, pi, :3] += weight*np.einsum(
                    'fij,j->fi', matrices[:, names[bone.attrib['name']]], rest)[:, :3]
            result[:, ci, pi, 3] = float(point.attrib['radius'])
        tapered |= result[0, ci, 0, 3] != result[0, ci, 1, 3]
    return result, tapered


def native_motion(args, data):
    from baker.skeleton import parse_skeljson
    from baker.animation import parse_animjson, skin_matrices
    rig = parse_skeljson(json.loads(args.skeleton.read_text(encoding='utf-8-sig')))
    anim = parse_animjson(json.loads(args.animation.read_text(encoding='utf-8-sig')))
    if anim['boneCount'] != rig['boneCount']:
        raise ValueError('animation/skeleton bone count mismatch')
    start = max(anim['start'], args.start)
    end = min(anim['frames'], args.end if args.end is not None else anim['frames'])
    if not start < end:
        raise ValueError('empty animation interval')
    matrices = np.array([skin_matrices(rig, anim, f) for f in range(start, end)])
    rest = decode_positions(data)
    weights = data['bone_weights'].reshape(-1, 4).astype(float)
    bones = data['bone_indices'].reshape(-1, 4).astype(int)
    if weights.shape != (len(rest), 4) or bones.max() >= rig['boneCount']:
        raise ValueError('missing/invalid cloth skinning')
    if not np.allclose(weights.sum(1), 1, atol=1e-6):
        raise ValueError('cloth skinning weights do not sum to 1')
    anchors = np.zeros((len(matrices), len(rest), 3))
    ph = np.column_stack((rest, np.ones(len(rest))))
    for k in range(4):
        anchors += np.einsum('fvij,vj->fvi', matrices[:, bones[:, k]], ph)[..., :3]*weights[:, k, None]
    if args.capsules:
        if not args.body:
            raise ValueError('--body is required with --capsules')
        capsules, tapered = capsule_tracks(args.capsules, args.body, rig, matrices)
    else:
        capsules, tapered = np.empty((len(anchors), 0, 2, 4)), False
    return anchors, capsules, list(range(start, end)), dict(animation=anim['name'],
            animation_sampling='existing offline nearest-key sampler; supplied fps',
            capsule_frame_convention='workspace authored row-major x-axis',
            tapered_capsules_approximate=bool(tapered))


def render_output(output, positions, anchors, capsules, tri, rows, heat, fps, title):
    edges = np.unique(np.sort(np.vstack((tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]])), axis=1), axis=0)
    # Store all frames numerically. Limit HTML playback to ~90 frames, retaining worst frame.
    worst = max(range(len(rows)), key=lambda i: max(rows[i]['vertex_penetration_m'], rows[i]['interior_penetration_m']))
    worst_strain = max(range(len(rows)), key=lambda i: rows[i]['max_stretch_strain'])
    preview_frames = min(90, max(2, 300000//len(positions[0])))
    keep = np.unique(np.r_[np.linspace(0, len(rows)-1, min(preview_frames, len(rows))).astype(int), worst, worst_strain])
    payload = dict(positions=positions[keep].round(6).tolist(), anchors=anchors[keep].round(6).tolist(),
                   capsules=capsules[keep].round(6).tolist(), edges=edges.tolist(),
                   heat=heat[keep].round(6).tolist(), rows=[rows[i] for i in keep],
                   fps=fps if len(keep)==len(rows) else (len(keep)-1)*fps/max(len(rows)-1, 1))
    template = (HERE/'viewer.html').read_text(encoding='utf-8')
    content = template.replace('__TITLE__', html.escape(title)).replace('__DATA__', json.dumps(payload, separators=(',', ':'), allow_nan=False))
    (output/'replay.html').write_text(content, encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    for which, name, label in ((worst, 'worst_frame.png', 'penetration'),
                               (worst_strain, 'worst_stretch.png', 'stretch')):
        fig, axes = plt.subplots(1, 2, figsize=(12, 8))
        for ax, horizontal, direction in zip(axes, (0, 1), ('Front (X/Z)', 'Side (Y/Z)')):
            ax.add_collection(LineCollection(anchors[which, edges][:, :, [horizontal, 2]], colors='#999999', linewidths=.25, alpha=.3))
            ax.add_collection(LineCollection(positions[which, edges][:, :, [horizontal, 2]], colors='#227eaf', linewidths=.3))
            for cap in capsules[which]:
                ax.plot(cap[:, horizontal], cap[:, 2], color='#36a075', linewidth=1)
                for point in cap:
                    ax.add_patch(plt.Circle(point[[horizontal, 2]], point[3], fill=False, color='#36a075'))
            bad = heat[which] > .0005
            ax.scatter(positions[which, bad, horizontal], positions[which, bad, 2], color='#e57432', s=5)
            ax.autoscale(); ax.set_aspect('equal'); ax.set_title(direction); ax.set_xlabel('meters')
        fig.suptitle(f'Approximate CPU cloth | worst {label} frame {rows[which].get("source_frame",which)}')
        fig.tight_layout(); fig.savefig(output/name, dpi=150); plt.close(fig)
    return worst


def simulate(args):
    output = args.output.resolve()
    input_paths = [p for p in (args.payload, args.mesh, args.motion, args.skeleton, args.animation, args.capsules) if p]
    if any(p.resolve().is_relative_to(output) for p in input_paths):
        raise ValueError('output must not contain any input files')
    if (output/'report.json').exists():
        raise ValueError('output already contains a report; choose a fresh output directory')
    data = read(args.payload)
    check_structure(data)
    mesh = json.loads(args.mesh.read_text(encoding='utf-8-sig'))
    mapping = data['render_to_sim'].astype(int)
    if len(np.unique(mapping)) != data['vertex_count']:
        raise ValueError('only direct simulation with all simulation vertices mapped is supported')
    vertices = np.asarray(mesh['positions'], float)
    if len(mapping) != len(vertices) or not np.isfinite(vertices).all():
        raise ValueError('mesh/render mapping mismatch')
    quant_error = float(np.linalg.norm(decode_positions(data)[mapping]-vertices, axis=1).max())
    if quant_error > .0002:
        raise ValueError('mesh and payload rest positions differ by more than 0.2 mm')
    package = None
    package_file = args.mesh.parent/'package.json'
    if package_file.is_file():
        package = json.loads(package_file.read_text(encoding='utf-8'))
        package_meshes = [m for mm in package['metadata'] for m in mm['meshes'] if m['Guid'] == mesh['guid']]
        if len(package_meshes) != 1 or package_meshes[0]['UnknownFloat1'] != args.multiplier:
            raise ValueError('mesh or distance multiplier differs from extracted package metadata')
        if 'files' in package:
            for p in (args.payload, args.mesh):
                if package['files'].get(p.name) != digest(p):
                    raise ValueError('extracted payload/mesh hash differs from package manifest')
        # Record snapshot identity; source TPAC may have moved since extraction.
        input_paths.append(package_file)
    indices = np.asarray(mesh['indices'], int).reshape(-1, 3)
    if not len(indices) or indices.min() < 0 or indices.max() >= len(mapping):
        raise ValueError('invalid mesh triangle indices')
    tri = mapping[indices]
    settings = Settings(fps=args.fps, substeps=args.substeps, iterations=args.iterations,
                        damping=args.damping, stretch=args.stretch, bend=args.bend,
                        shear=args.shear, anchor=args.anchor, gravity=args.gravity,
                        thickness=args.thickness, dummy_collision=not args.no_dummy,
                        penetration_tolerance=args.penetration_tolerance,
                        strain_tolerance=args.strain_tolerance)
    settings.validate()
    if not np.isfinite(args.multiplier) or args.multiplier < 0:
        raise ValueError('multiplier must be finite and nonnegative')
    if args.motion:
        if args.skeleton or args.animation or args.capsules or args.body:
            raise ValueError('--motion cannot be combined with skeleton/animation/capsules/body')
        with np.load(args.motion, allow_pickle=False) as archive:
            anchors = archive['anchors'].copy()
            capsules = archive['capsules'].copy() if 'capsules' in archive else np.empty((len(anchors), 0, 2, 4))
        source_frames = list(range(len(anchors)))
        meta = dict(animation_sampling='provided NPZ; fps supplied by caller')
    else:
        if not args.skeleton or not args.animation:
            raise ValueError('provide --motion, or both --skeleton and --animation')
        anchors, capsules, source_frames, meta = native_motion(args, data)
    if args.warmup < 0:
        raise ValueError('warmup must be nonnegative')
    combined_anchors = np.concatenate((np.repeat(anchors[:1], args.warmup, axis=0), anchors))
    combined_caps = np.concatenate((np.repeat(capsules[:1], args.warmup, axis=0), capsules))
    positions, rows, heat = Simulator(data, tri, settings).run(combined_anchors, combined_caps,
                                                            data['max_distances']*args.multiplier)
    positions, rows, heat = positions[args.warmup:], rows[args.warmup:], heat[args.warmup:]
    for i, row in enumerate(rows):
        row.update(frame=i, time_s=i/settings.fps, source_frame=source_frames[i])
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output/'frames.npz', positions=positions, anchors=anchors,
                        capsules=capsules, triangles=tri, penetration=heat)
    worst = render_output(output, positions, anchors, capsules, tri, rows, heat, args.fps, mesh['name'])
    maxima = {key: max(r[key] for r in rows) for key in rows[0] if key not in ('frame', 'time_s', 'source_frame')}
    exceeded = (max(maxima['vertex_penetration_m'], maxima['interior_penetration_m']) > settings.penetration_tolerance
                or maxima['max_stretch_strain'] > settings.strain_tolerance)
    no_collision = capsules.shape[1] == 0
    status = 'incomplete' if no_collision else ('needs_review' if exceeded else 'within_thresholds')
    report = dict(status=status, scope='approximate_cpu_diagnostic', game_solver_used=False,
                  game_verified=False, mesh=mesh['name'], lod=mesh['lod'], frames=len(rows),
                  settings=asdict(settings), distance_multiplier=args.multiplier, warmup_frames=args.warmup,
                  inputs=[dict(path=str(p.resolve()), sha256=digest(p)) for p in input_paths],
                  rest_quantization_error_m=quant_error, collision_capsules=capsules.shape[1],
                  worst_penetration_frame=source_frames[worst], maxima=maxima, frame_metrics=rows,
                  worst_stretch_frame=source_frames[max(range(len(rows)), key=lambda i: rows[i]['max_stretch_strain'])],
                  package_snapshot=dict(tpac=package['tpac'], sha256=package['sha256'],
                      material=package_meshes[0]['ClothingMaterial']) if package else None,
                  limitations=['No engine CPU parameter conversion or global entity inertia/wind.',
                               'CPU float64, no GPU position compression; different pin/travel enforcement.',
                               'No continuous collision detection, self-collision, render proxy mapping, horse or body triangle collision.',
                               'Four interior samples diagnose risk, not all triangle/capsule intersections.',
                               'Solver parameters are diagnostic settings, not imported game material values.'], **meta)
    report['limitations'].append('Fixed vertex capsule overlap is informational; fixed surfaces may intentionally lie inside capsules.')
    (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(dict(status=status, output=str(output), maxima=maxima), indent=2))
    return 2 if no_collision else (1 if exceeded else 0)


def extract(args):
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('extract requires an empty output directory')
    if not args.probe.is_file() or not args.tpac.is_file():
        raise ValueError('missing probe DLL or TPAC')
    output.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(['dotnet', str(args.probe.resolve()), str(args.tpac.resolve()),
                              args.metamesh, '--dump-segments', str(output)], capture_output=True, text=True, check=True)
    metadata = json.loads(result.stdout)
    if not metadata or not list(output.glob('*.mesh.json')):
        raise ValueError('no cloth meshes found for exact metamesh name')
    (output/'package.json').write_text(json.dumps(dict(tpac=str(args.tpac.resolve()),
                sha256=digest(args.tpac), metadata=metadata,
                files={p.name:digest(p) for p in output.iterdir() if p.is_file()}), indent=2), encoding='utf-8')
    print(f'Extracted final TPAC cloth data to {output}')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    ex = commands.add_parser('extract', help='read-only extraction using NativeClothProbe')
    ex.add_argument('--tpac', type=Path, required=True)
    ex.add_argument('--metamesh', required=True)
    ex.add_argument('--probe', type=Path, required=True)
    ex.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('simulate', help='simulate one direct-cloth mesh and motion')
    for key in ('payload', 'mesh', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--motion', type=Path, help='NPZ: anchors[F,N,3], optional capsules[F,C,2,4]')
    for key in ('skeleton', 'animation', 'capsules'):
        p.add_argument('--'+key, type=Path)
    p.add_argument('--body')
    p.add_argument('--fps', type=float, required=True, help='actual source animation sample rate')
    p.add_argument('--multiplier', type=float, required=True, help='mesh max-distance multiplier from final metadata')
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--end', type=int)
    p.add_argument('--warmup', type=int, default=30)
    for key in ('substeps', 'iterations'):
        p.add_argument('--'+key, type=int, default=getattr(Settings(), key))
    for key in ('damping', 'stretch', 'shear', 'bend', 'anchor', 'gravity', 'thickness', 'penetration_tolerance', 'strain_tolerance'):
        p.add_argument('--'+key.replace('_', '-'), type=float, default=getattr(Settings(), key))
    p.add_argument('--no-dummy', action='store_true')
    args = parser.parse_args()
    try:
        return extract(args) if args.command == 'extract' else simulate(args)
    except (ValueError, OSError, AssertionError, KeyError, IndexError, struct.error, FloatingPointError, subprocess.CalledProcessError) as e:
        print(f'cloth diagnostic error: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
