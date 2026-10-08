"""Install only this new module after verifying release report and delivery bytes."""
import argparse
import json
import shutil
import zipfile
from pathlib import Path
from paths import ROOT, MODULE, GAME, MOD_ID, VERSION
from verify_release import sha

def install(game_root):
    report = json.loads((ROOT / 'reports/release_validation.json').read_text(encoding='utf-8'))
    if report['status'] != 'pass' or report['version'] != VERSION:
        raise ValueError('Release report has not passed for this version')
    module = MODULE.resolve()
    files = {p.relative_to(module).as_posix(): p for p in module.rglob('*') if p.is_file() and p.name != '.gitkeep'}
    if set(files) != set(report['module_files']):
        raise ValueError('Module file list changed after validation')
    for relative, path in files.items():
        if path.is_symlink() or sha(path) != report['module_files'][relative]:
            raise ValueError('Unvalidated or linked module file: ' + relative)
    archive = ROOT / 'dist' / (MOD_ID + '_Mod.zip')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Corrupt delivery')
        if set(z.namelist()) != {MOD_ID + '/' + p for p in files}:
            raise ValueError('Delivery file list differs')
        for relative, path in files.items():
            if z.read(MOD_ID + '/' + relative) != path.read_bytes():
                raise ValueError('Delivery differs from module: ' + relative)
    modules_root = (game_root / 'Modules').resolve(strict=True)
    destination = modules_root / MOD_ID
    if destination.parent != modules_root or MOD_ID != 'BeautyBanners':
        raise ValueError('Unsafe installation destination')
    # Initial release: preserve any existing directory and require a deliberate update workflow.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Initial-release target already exists; preserve it before performing an update')
    installed = {}
    for relative, source in sorted(files.items()):
        target = (destination / relative).resolve()
        if not target.is_relative_to(destination):
            raise ValueError('Install path outside this module')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        digest = sha(target)
        if digest != report['module_files'][relative]:
            raise ValueError('Installed bytes differ: ' + relative)
        installed[relative] = digest
    result = {'status': 'pass', 'version': VERSION, 'installed_to': str(destination),
              'file_hashes': installed, 'mod_archive_sha256': sha(archive),
              'source_archive_sha256': sha(ROOT / 'dist' / (MOD_ID + '_Source.zip')),
              'game_launched': False, 'native_modified': False}
    (ROOT / 'reports/installation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Installed and byte-verified', len(installed), 'files:', destination)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=GAME)
    args = parser.parse_args()
    install(args.game_root)
