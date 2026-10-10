"""Prepare actual delivery manifest after package and editable-source QA."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from audit_cloth_payload import audit
payload=audit()
assert not payload['missing_direct_cloth_meshes'], 'Cloth payload missing: do not publish another parameter-only cloth fix. See reports/cloth_payload_diagnosis.json.'
from verify_cooked_cloth import verify
cooked=verify(ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac')
report_path=ROOT/'reports/release_validation.json';report=json.loads(report_path.read_text())
source=json.loads((ROOT/'reports/source_validation.json').read_text());assert source['status']=='pass'
package=ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
assert report['status']=='pass' and report['final_package_sha256']==hashlib.sha256(package.read_bytes()).hexdigest()
preview=json.loads((ROOT/'reports/final_preview_manifest.json').read_text());assert preview['package_sha256']==report['final_package_sha256']
assert json.loads((ROOT/'reports/native_provenance.json').read_text())['status']=='pass'
cloth=json.loads((ROOT/'reports/cloth_validation.json').read_text())
assert cloth['status']=='pass' and cloth['final_package_sha256']==report['final_package_sha256']
proportions=json.loads((ROOT/'reports/proportion_validation.json').read_text())
assert proportions['status']=='pass' and proportions['final_package_sha256']==report['final_package_sha256']
report['proportion_repair_verified']=True
travel=json.loads((ROOT/'reports/veil_travel_validation.json').read_text())
assert travel['status']=='pass' and travel['final_package_sha256']==report['final_package_sha256']
report['sleeve_travel_feasibility_checked']=True
report['sleeve_distance_scale_assumption']=travel['assumption']
report['editable_source_verified']=True
activation=json.loads((ROOT/'reports/cloth_activation_validation.json').read_text())
assert activation['status']=='pass' and activation['final_package_sha256']==report['final_package_sha256']
report['native_tassel_activation_alignment_verified']=True
report['baseline_reason']='v1.0.3 own cooked cloth payload revision'
report['baseline_package_sha256']=cooked['baseline_package_sha256']
report['cooked_cloth_payloads_verified']=True
report['cooked_cloth_format_native_samples']=len(cooked['native_samples'])
report['visual_review']={'reviewed':'final eye/lash close-ups, rest front/side/back and worst native motion/contact frames','result':'reviewed; sleeve veils remain rigidly skinned in previews because the game cloth solver was not run; skirt leg proxy contacts remain for user testing','game_verified':False}
report_path.write_text(json.dumps(report,indent=2))
files=['README.md','mod.json']
if (ROOT/'CHANGELOG.md').is_file():files.append('CHANGELOG.md')
for folder in ['input','source','tools','module','reports']:
    for p in sorted((ROOT/folder).rglob('*')):
        if not p.is_file() or any(part in ['__pycache__','obj','bin'] for part in p.relative_to(ROOT).parts):continue
        if p.name=='.gitkeep' or p.suffix in ['.pyc','.blend1','.log']:continue
        if p.name=='installation_validation.json':continue
        if folder=='module' and p.suffix=='.tpac':continue
        if folder=='reports' and p.suffix=='.png' and not p.name.startswith(('final_','proportion_')):continue
        files.append(p.relative_to(ROOT).as_posix())
cfg={'id':'ShengxiuCollection','source_files':files,'package':'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac','validation_report':'reports/release_validation.json'}
from shared_cloth import SHARED
cfg['shared_source_files']=['tools/cloth_compiler/'+p.name for p in sorted(SHARED.iterdir()) if p.is_file() and p.suffix in ['.py','.cs','.csproj','.md']]
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2))
print('DELIVERY_MANIFEST_READY',len(files),'files plus textures')
