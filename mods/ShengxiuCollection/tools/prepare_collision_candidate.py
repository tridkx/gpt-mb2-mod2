"""Build and verify v1.1.1 collision-isolation candidate from preserved v1.1.0."""
import hashlib,json,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION='v1.1.1'
BASE_SHA='616b97186624b1cc220385e017224e2ad8e3d5046fe10d276cc1b1a8e6ad1708'
module=ROOT/'module/ShengxiuCollection'
package=module/'AssetPackages/sx_mingyu.tpac'
baseline=ROOT/'build/collision_baseline_v1.1.0/sx_mingyu.tpac'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline.parent.mkdir(exist_ok=True)
if not baseline.exists():
 assert sha(package)==BASE_SHA
 shutil.copy2(package,baseline)
assert sha(baseline)==BASE_SHA
candidate=ROOT/'build/collision_candidate_v1.1.1.tpac'
subprocess.run(['dotnet',str(ROOT/'build/collision_isolation/CollisionIsolation.dll'),str(baseline),str(candidate)],check=True)
names=['sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs']
probe=ROOT/'build/cloth_probe/NativeClothProbe.dll'
def inspect(p,dest):return json.loads(subprocess.check_output(['dotnet',str(probe),str(p),*names,'--dump-segments',str(dest)],encoding='utf-8'))
before_dump=ROOT/'build/collision_baseline_dump';after_dump=ROOT/'build/collision_candidate_dump'
before=inspect(baseline,before_dump);after=inspect(candidate,after_dump)
blob_hashes={p.name:sha(p) for p in before_dump.glob('*.bin')}
assert len(blob_hashes)==8
assert blob_hashes=={p.name:sha(p) for p in after_dump.glob('*.bin')}
for old,new in zip(before,after):
 assert old['Name']==new['Name']
 expected=dict(old)
 if old['Name'] in names[:2]:expected['body']=''
 assert expected==new,(old['Name'],'Unexpected metadata, geometry or payload change')
assert sum('uses_cloth_simulation' in m['Flags'] for mm in after for m in mm['meshes'])==4
ws=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
# Independent metadata/material/vertex-alpha audit of final candidate.
audit=json.loads(subprocess.check_output([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(candidate),'--cloth-vertex-alpha'],encoding='utf-8'))
assert audit['status']=='pass',audit
cfg=json.loads((ROOT/'mod.json').read_text())
collection=json.loads((ROOT/'reports/collection_release_validation.json').read_text())
others={p.name:sha(p) for p in (module/'AssetPackages').glob('*.tpac') if p!=package}
assert all(sha(ROOT/r['path'])==r['sha256'] for r in collection['packages'] if r['prefix']!='sx_mingyu')
shutil.copy2(candidate,package)
descriptor=ET.parse(module/'SubModule.xml');descriptor.find('Version').set('value',VERSION)
ET.indent(descriptor,space='  ');descriptor.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
assert len(ET.parse(module/'ModuleData/items.xml').getroot())==9
assert others=={p.name:sha(p) for p in (module/'AssetPackages').glob('*.tpac') if p!=package}
diagnostic=json.loads((ROOT/'build/cloth_lift_diagnostic.json').read_text())
report={'status':'pass','version':VERSION,'check_scope':'offline_single_variable_candidate_checks','final_package_sha256':sha(package),'baseline_package_sha256':BASE_SHA,'candidate_purpose':'Isolate native human_body collision projection as source of Mingyu lift; retain cloth simulation','changes':{'sx_mingyu_head.body':['human_body',''],'sx_mingyu_body.body':['human_body','']},'all_56_mesh_metadata_and_geometry_hashes_identical':True,'all_metamesh_segment_checksums_identical':True,'cloth_and_editor_blob_sha256':blob_hashes,'all_four_cloth_payloads_and_parameters_identical':True,'other_set_package_hashes_unchanged':others,'registered_items':9,'package_audit':audit,'cpu_diagnostic':diagnostic,'game_test_verified':False,'limitations':'Collision isolation candidate, not confirmed final repair. Hair, skirt and sleeve veils retain cloth but have no human_body collision; clipping can increase. CPU capsule interpretation is diagnostic, not engine simulation. Test inventory idle then running and mounted poses.'}
for row in collection['packages']:
 if row['prefix']=='sx_mingyu':row['sha256']=sha(package);row['report']='reports/collision_candidate_validation.json'
report['packages']=collection['packages']
(ROOT/'reports/collision_candidate_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
cfg['validation_report']='reports/collision_candidate_validation.json'
cfg['source_files']=sorted(set(cfg['source_files'])|{'reports/collision_candidate_validation.json','reports/user_feedback_lift_2026-10-09.json','tools/CollisionIsolation.cs','tools/CollisionIsolation.csproj','tools/prepare_collision_candidate.py','tools/diagnose_cloth_lift.py'})
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
print('CANDIDATE_VERIFIED',VERSION,sha(package),'4 cloth meshes, 56 preserved geometry streams; other outfits unchanged')
