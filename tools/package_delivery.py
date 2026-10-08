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
    deliveries = [
        ('Mod', [(project_file(root, p.relative_to(root)), name + '/' + p.relative_to(module).as_posix())
                 for p in module.rglob('*') if p.is_file() and p.name != '.gitkeep']),
        ('Source', [(p, p.relative_to(root).as_posix()) for p in sources]),
    ]
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
