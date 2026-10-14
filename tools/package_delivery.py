"""Package one configured mod and verify archive bytes; never install."""
import argparse
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from project_paths import resolve_project
WORKSPACE = Path(__file__).resolve().parents[1]


def validate_name(name):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
        raise ValueError('Mod name must contain only letters, digits, underscores or hyphens')


def load_project(name):
    validate_name(name)
    root = resolve_project(WORKSPACE, name)
    config = json.loads((root / 'mod.json').read_text(encoding='utf-8'))
    if config['id'] != name:
        raise ValueError('Mod configuration ID differs from directory name')
    return root, config


def project_file(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Missing file or path outside mod: {relative}')
    return path


def package(name, version, check_only=False):
    root, config = load_project(name)
    module = root / 'module' / name
    descriptor = ET.parse(project_file(root, f'module/{name}/SubModule.xml'))
    if descriptor.find('Id').get('value') != name or descriptor.find('Version').get('value') != version:
        raise ValueError('Module ID/version differs from requested package')
    sources = [project_file(root, p) for p in config['source_files']]
    sources.extend(project_file(root, p.relative_to(root)) for p in (root / 'tex').rglob('*') if p.is_file() and p.name != '.gitkeep')
    shared_sources = []
    for relative in config.get('shared_source_files', []):
        path = (WORKSPACE / relative).resolve()
        if not path.is_relative_to((WORKSPACE / 'tools').resolve()) or not path.is_file():
            raise ValueError(f'Shared source must be a file inside workspace tools: {relative}')
        shared_sources.append((path, 'workspace_tools/' + path.relative_to(WORKSPACE / 'tools').as_posix()))
    # Opt-in checks run before either archive writing or installer preflight.
    # The unchanged final TPAC plus all diagnostic inputs form the cache key.
    diagnostic_sources = []
    # Collections retain independent character TPACs and diagnostic configurations.
    # Check the scoped components on both package and installer preflight entries.
    if config.get('collection_components'):
        from cloth_simulator.pipeline import ensure_diagnostics
        for component_id in config['collection_components']:
            validate_name(component_id)
            component = (root / component_id).resolve()
            if component.parent != root.resolve():
                raise ValueError('Collection component outside collection')
            component_config = json.loads(project_file(component, 'mod.json').read_text(encoding='utf8'))
            if component_config['id'] != component_id:
                raise ValueError('Collection component ID mismatch')
            original = project_file(component, component_config['package'])
            relative = original.relative_to(component / 'module' / component_id)
            assembled = project_file(root, (module / relative).relative_to(root))
            if original.read_bytes() != assembled.read_bytes():
                raise ValueError('Collection TPAC differs from component: ' + component_id)
            if 'cloth_diagnostics' in component_config:
                ensure_diagnostics(component, component_config)
    if 'cloth_diagnostics' in config:
        from cloth_simulator.pipeline import ensure_diagnostics, delivery_files
        diagnostic = ensure_diagnostics(root, config)
        diagnostic_sources, diagnostic_shared = delivery_files(root, diagnostic)
        shared_sources.extend(diagnostic_shared)
    deliveries = [
        ('Mod', [(project_file(root, p.relative_to(root)), name + '/' + p.relative_to(module).as_posix())
                 for p in module.rglob('*') if p.is_file() and p.name != '.gitkeep']),
        ('Source', [(p, p.relative_to(root).as_posix()) for p in sources] + shared_sources + diagnostic_sources),
    ]
    # Configured source lists may already contain the automatically added files.
    deduplicated = []
    for kind, files in deliveries:
        unique = {}
        for file, entry in files:
            if entry in unique and unique[entry].resolve() != file.resolve():
                raise ValueError(f'Conflicting archive entry: {entry}')
            unique[entry] = file
        deduplicated.append((kind, [(file, entry) for entry, file in unique.items()]))
    deliveries = deduplicated
    if check_only:
        print(f'{name} {version}: package inputs valid; no archives written.')
        return
    (root / 'dist').mkdir(exist_ok=True)
    for kind, files in deliveries:
        archive = root / 'dist' / f'{name}_{kind}.zip'
        temporary = archive.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for file, entry in files:
                z.write(file, entry)
        with zipfile.ZipFile(temporary) as z:
            if z.testzip() is not None:
                raise ValueError(f'Corrupt archive: {temporary}')
            for file, entry in files:
                if z.read(entry) != file.read_bytes():
                    raise ValueError(f'Archive differs: {entry}')
        temporary.replace(archive)
    print(f'{name} {version}: module and editable source archives verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    package(args.mod, args.version, args.check_only)
