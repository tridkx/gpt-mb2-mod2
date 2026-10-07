"""Restore the archived pre-trial module; keep experimental project assets."""
from pathlib import Path, PurePosixPath
import hashlib, json, shutil, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/TianxiangT5')
VERSION = 'v1.3.1'
EXPECTED = '7d3fa2e062fd29fd0c9ffa31c273f0a8f42a1dde29ee9b553601c90af22ce6e4'
sha = lambda data: hashlib.sha256(data).hexdigest()

# Preserve the latest deliveries under their own version before any restore.
for kind in ['Mod', 'Source']:
    current = ROOT / f'dist/TianxiangT5_{kind}.zip'
    backup = ROOT / f'dist/TianxiangT5_v1.5.3_{kind}.zip'
    if not backup.exists():
        shutil.copy2(current, backup)
    else:
        assert sha(current.read_bytes()) == sha(backup.read_bytes()), 'Existing archive differs'

archive = ROOT / f'dist/TianxiangT5_{VERSION}_Mod.zip'
files = {}
with zipfile.ZipFile(archive) as z:
    for entry in z.infolist():
        if entry.is_dir():
            continue
        path = PurePosixPath(entry.filename)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] == 'TianxiangT5' and len(path.parts) > 1
        relative = Path(*path.parts[1:])
        dest = (TARGET / relative).resolve()
        assert dest.is_relative_to(TARGET.resolve())
        files[relative] = z.read(entry)
assert ET.fromstring(files[Path('SubModule.xml')]).find('Version').attrib['value'] == VERSION
assert sha(files[Path('AssetPackages/tx5.tpac')]) == EXPECTED
before = sha((TARGET / 'AssetPackages/tx5.tpac').read_bytes())
for relative, data in files.items():
    dest = TARGET / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    assert sha(dest.read_bytes()) == sha(data)

config = Path('C:/Users/DKX/Documents/Mount and Blade II Bannerlord/Configs/engine_config.txt')
setting = next(line.strip() for line in config.read_text().splitlines()
               if line.strip().startswith('enable_cloth_simulation ='))
report = {
    'status': 'rolled back and byte verified',
    'trial_status': 'stopped at user request; sleeve pulling unresolved in v1.5.3',
    'installed_version': VERSION,
    'project_trial_version_retained': 'v1.5.3',
    'module': str(TARGET),
    'restored_from': str(archive),
    'previous_installed_package_sha256': before,
    'installed_package_sha256': EXPECTED,
    'verified_module_files': len(files),
    'latest_trial_archives_preserved': 'v1.5.3',
    'global_cloth_setting_observed': setting,
    'global_cloth_setting_changed': False,
    'game_started': False,
}
(ROOT / 'reports/cloth_pause_and_rollback.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
