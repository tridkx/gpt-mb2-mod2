"""Verify the UI-only repair release against the accepted v0.1.2 assets."""
from pathlib import Path
import json
import hashlib
import zipfile
import numpy as np
import sys
from lxml import etree as ET
from verify_registration import canonical, validate_registration

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[2] / 'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson

sha = lambda b: hashlib.sha256(b).hexdigest()
cfg = json.loads((ROOT / 'tools/model_config.json').read_text())
assert cfg['ui_preview_repair'] and cfg['skin_min_scale'] == 1.1
history = ROOT / 'reports/history/v0.1.2'
baseline_report = json.loads((history / 'release_validation.json').read_text())
archive = ROOT / 'dist/REAdaWongRace_v0.1.2_Mod.zip'
if not archive.exists():
    archive = ROOT / 'dist/REAdaWongRace_Mod.zip'
module = ROOT / 'module' / cfg['id']
runtime_relative = 'bin/Win64_Shipping_Client/REAdaWongRace.UIRuntime.dll'
parser = ET.XMLParser(remove_blank_text=True, remove_comments=True)
with zipfile.ZipFile(archive) as z:
    old = ET.fromstring(z.read(cfg['id'] + '/SubModule.xml'), parser)
    assert old.find('Version').get('value') == 'v0.1.2'
    new = ET.parse(str(module / 'SubModule.xml'), parser).getroot()
    runtime = new.find('SubModules/SubModule')
    assert len(new.find('SubModules')) == 1
    assert runtime.find('DLLName').get('value') == Path(runtime_relative).name
    assert runtime.find('SubModuleClassType').get('value') == 'REAdaWongRace.UIProbe.SubModule'
    new.find('SubModules').remove(runtime)
    old.find('Version').set('value', cfg['version'])
    assert canonical(old) == canonical(new)
    expected = {x[len(cfg['id']) + 1:] for x in z.namelist()}
    actual = {p.relative_to(module).as_posix() for p in module.rglob('*') if p.is_file()}
    assert actual == expected | {runtime_relative}
    for name in z.namelist():
        relative = name[len(cfg['id']) + 1:]
        if relative != 'SubModule.xml':
            assert z.read(name) == (module / relative).read_bytes(), relative
assert (module / runtime_relative).read_bytes() == (ROOT / 'build/ui_runtime_dll' / Path(runtime_relative).name).read_bytes()
package_sha = sha((module / 'AssetPackages/adar.tpac').read_bytes())
assert package_sha == baseline_report['final_package_sha256']
source_archive = ROOT / 'dist/REAdaWongRace_v0.1.2_Source.zip'
if not source_archive.exists():
    source_archive = ROOT / 'dist/REAdaWongRace_Source.zip'
with zipfile.ZipFile(source_archive) as z:
    assert json.loads(z.read('tools/model_config.json'))['version'] == 'v0.1.2'
    for directory in ['source', 'tex']:
        for p in (ROOT / directory).rglob('*'):
            if p.is_file() and p.suffix in ['.blend', '.fbx', '.png']:
                assert sha(z.read(p.relative_to(ROOT).as_posix())) == sha(p.read_bytes()), p
captures = json.loads((history / 'ui_runtime_capture.json').read_text())
pose = next(row['record'] for row in captures if row['record']['kind'] == 'ada_pose')
actual_rest = np.array([b['rest_local_unmapped'] for b in pose['bones']]).reshape(28, 4, 4).transpose(0, 2, 1)
native = parse_skeljson(json.loads((ROOT / 'reports/human_skeleton.json').read_text()))
ada = parse_skeljson(json.loads((ROOT / 'reports/final_skeleton.json').read_text()))
native_error = float(np.max(abs(actual_rest - native['restLocal'])))
ada_error = float(np.max(abs(actual_rest - ada['restLocal'])))
assert pose['skeleton'] == 'human_skeleton' and native_error < 2e-6 and ada_error > .01
registration = validate_registration(ROOT)
report = dict(status='pass', version=cfg['version'], final_package_sha256=package_sha,
    captured_screen=pose['screen'], captured_skeleton=pose['skeleton'],
    captured_action_set=pose['action_set'], runtime_rest_error_vs_native=native_error,
    runtime_rest_error_vs_ada=ada_error, module_changes=['SubModule.xml', runtime_relative],
    accepted_geometry_bind_rig_weights_materials_sources_unchanged=True,
    compiled_runtime=True, repair_scope='Ada AgentVisuals reachable only from non-mission UI',
    runtime_after_repair_verified=False)
(ROOT / 'reports/ui_runtime_validation.json').write_text(json.dumps(report, indent=2))
release = dict(baseline_report)
release.update(version=cfg['version'], status='pass', registration=registration,
    check_scope='UI repair assembly and exact accepted asset comparison; pre-repair runtime evidence',
    inherited_asset_validation='reports/history/v0.1.2/release_validation.json',
    baseline_package_sha256=package_sha, baseline_reason=cfg['validation_baseline_reason'],
    ui_runtime_validation=report, game_test_verified=False)
(ROOT / 'reports/release_validation.json').write_text(json.dumps(release, indent=2))
print(json.dumps(report, indent=2))
