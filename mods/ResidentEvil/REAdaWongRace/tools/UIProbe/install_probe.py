"""Install a reversible read-only diagnostic overlay on the accepted v0.1.2."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
ID = 'REAdaWongRace'
MODULE = ROOT / 'module' / ID
INSTALLED = GAME / 'Modules' / ID


def sha(data):
    return hashlib.sha256(data).hexdigest()


def install():
    result = subprocess.run(['powershell', '-NoProfile', '-Command',
        "@(Get-Process | Where-Object ProcessName -Match 'Bannerlord|TaleWorlds').Count"],
        check=True, capture_output=True, text=True)
    assert int(result.stdout.strip()) == 0, 'Exit the game and launcher before installing the probe'
    assert ET.parse(GAME / 'Modules/Native/SubModule.xml').find('Version').get('value') == 'v1.4.8'
    dll = ROOT / 'build/ui_probe_dll/REAdaWongRace.UIProbe.dll'
    assert dll.is_file()
    history = ROOT / 'reports/history/v0.1.2'
    history.mkdir(exist_ok=True)
    with zipfile.ZipFile(ROOT / 'dist/REAdaWongRace_Mod.zip') as z:
        descriptor = z.read(ID + '/SubModule.xml')
        xml = ET.fromstring(descriptor)
        assert xml.find('Version').get('value') == 'v0.1.2'
        assert not list(xml.find('SubModules'))
        for name in z.namelist():
            rel = Path(name).relative_to(ID)
            assert sha(z.read(name)) == sha((MODULE / rel).read_bytes()), ('Workspace changed', rel)
            assert sha(z.read(name)) == sha((INSTALLED / rel).read_bytes()), ('Installed module changed', rel)
    baseline = history / 'SubModule.xml'
    assert not baseline.exists() or baseline.read_bytes() == descriptor
    baseline.write_bytes(descriptor)
    for name in ['release_validation.json', 'installation_validation.json']:
        target = history / name
        if not target.exists():
            shutil.copy2(ROOT / 'reports' / name, target)
    sub = ET.SubElement(xml.find('SubModules'), 'SubModule')
    ET.SubElement(sub, 'Name', value='Ada UI Read-only Probe')
    ET.SubElement(sub, 'DLLName', value=dll.name)
    ET.SubElement(sub, 'SubModuleClassType', value='REAdaWongRace.UIProbe.SubModule')
    ET.SubElement(sub, 'Tags')
    ET.indent(xml, space='  ')
    xmlbytes = ET.tostring(xml, encoding='utf-8', xml_declaration=True)
    binaryrel = Path('bin/Win64_Shipping_Client') / dll.name
    changes = {'SubModule.xml': xmlbytes, binaryrel.as_posix(): dll.read_bytes()}
    for rel in changes:
        if rel != 'SubModule.xml':
            assert not (MODULE / rel).exists() and not (INSTALLED / rel).exists(), 'Existing probe must be reviewed before replacing'
    overlay = ROOT / 'dist/REAdaWongRace_UIProbe.zip'
    with zipfile.ZipFile(overlay, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel, data in changes.items():
            z.writestr(ID + '/' + rel, data)
    with zipfile.ZipFile(overlay) as z:
        assert z.testzip() is None
        assert all(z.read(ID + '/' + rel) == data for rel, data in changes.items())
    for rel, data in changes.items():
        for directory in [MODULE, INSTALLED]:
            target = directory / rel
            assert target.resolve().is_relative_to(directory.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            assert target.read_bytes() == data
    report = dict(status='pass', version='v0.1.2', diagnostic_only=True,
        appearance_fix_applied=False, game_runtime_capture_verified=False,
        installed_module=str(INSTALLED), changed_files={rel:sha(data) for rel,data in changes.items()},
        accepted_asset_package_unchanged=True,
        baseline_descriptor='reports/history/v0.1.2/SubModule.xml',
        primary_release_archives_unchanged=True,
        overlay_archive_sha256=sha(overlay.read_bytes()),
        log_path='Documents/Mount and Blade II Bannerlord/REAdaWongRace/ui_probe_v1.jsonl')
    (ROOT / 'reports/ui_probe_installation.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    install()
