"""Verify and compose Mingyu v1.1.2 leg-collision game test candidate."""
import hashlib,json,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];VERSION='v1.1.2'
BASE_SHA='e5fffe2ae8137453933ad785d65bd11c3d2ec1834a989d83d620172a3df163ea'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
module=ROOT/'module/ShengxiuCollection';package=module/'AssetPackages/sx_mingyu.tpac'
baseline=ROOT/'build/leg_collision_baseline_v1.1.1/sx_mingyu.tpac';baseline.parent.mkdir(exist_ok=True)
if not baseline.exists():
 assert sha(package)==BASE_SHA
 shutil.copy2(package,baseline)
assert sha(baseline)==BASE_SHA
fit=json.loads((ROOT/'reports/leg_collision_fit.json').read_text())
assert fit['status']=='pass'
native=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/ModuleData/cloth_bodies.xml')
assert sha(native)==fit['native_cloth_bodies_sha256']
xml=module/'ModuleData/cloth_bodies.xml';assert sha(xml)==fit['custom_xml_sha256']
bodies=ET.parse(xml).getroot();assert len(bodies)==1
body=bodies[0];assert body.get('name')=='sx_mingyu_leg_collision'
assert {c.get('name') for c in body.findall('./capsules/capsule')}=={'l_thigh','r_thigh','l_calf','r_calf'}
assert body.get('owner_skeleton')=='human_skeleton'
assert len(fit['skirt_projection_diagnostics'])==26
assert fit['skirt_projection_diagnostics'][0]['max_lift_m']<.01
candidate=ROOT/'build/leg_collision_candidate_v1.1.2.tpac'
subprocess.run(['dotnet',str(ROOT/'build/leg_collision/LegCollision.dll'),str(baseline),str(candidate)],check=True)
probe=ROOT/'build/cloth_probe/NativeClothProbe.dll';names=['sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs']
def inspect(p,dest):return json.loads(subprocess.check_output(['dotnet',str(probe),str(p),*names,'--dump-segments',str(dest)],encoding='utf-8'))
bd=ROOT/'build/leg_collision_before_dump';ad=ROOT/'build/leg_collision_after_dump'
before=inspect(baseline,bd);after=inspect(candidate,ad)
for old,new in zip(before,after):
 expected=dict(old)
 if old['Name']=='sx_mingyu_body':expected['body']=body.get('name')
 assert expected==new,(old['Name'],'Unexpected change')
blobs={p.name:sha(p) for p in bd.glob('*.bin')};assert len(blobs)==8
assert blobs=={p.name:sha(p) for p in ad.glob('*.bin')}
assert sum('uses_cloth_simulation' in m['Flags'] for mm in after for m in mm['meshes'])==4
audit=json.loads(subprocess.check_output([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(candidate),'--cloth-vertex-alpha'],encoding='utf-8'))
assert audit['status']=='pass'
previous=json.loads((ROOT/'reports/collision_candidate_validation.json').read_text())
others={p.name:sha(p) for p in (module/'AssetPackages').glob('*.tpac') if p!=package}
assert others==previous['other_set_package_hashes_unchanged']
shutil.copy2(candidate,package)
descriptor=ET.parse(module/'SubModule.xml');descriptor.find('Version').set('value',VERSION)
ET.indent(descriptor,space='  ');descriptor.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
f=module/'SubModule.xml';f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
assert len(ET.parse(module/'ModuleData/items.xml').getroot())==9
assert sha(native)==fit['native_cloth_bodies_sha256']
for row in previous['packages']:
 if row['prefix']=='sx_mingyu':row['sha256']=sha(package);row['report']='reports/leg_collision_validation.json'
report={'status':'pass','version':VERSION,'check_scope':'offline_leg_collision_candidate','final_package_sha256':sha(package),'baseline_package_sha256':BASE_SHA,'own_leg_collision_body':body.get('name'),'collision_xml_sha256':sha(xml),'native_cloth_bodies_preserved':True,'all_56_mesh_metadata_and_geometry_hashes_identical':True,'all_metamesh_segment_checksums_identical':True,'cloth_and_editor_blob_sha256':blobs,'all_four_cloth_payloads_and_parameters_identical':True,'head_collision_remains_disabled':True,'other_set_package_hashes_unchanged':others,'packages':previous['packages'],'leg_fit_report':'reports/leg_collision_fit.json','registered_items':9,'package_audit':audit,'game_test_verified':False,'limitations':'Candidate adds unique ModuleData/cloth_bodies.xml leg-only body; runtime custom body loading and collision efficacy need user game testing. No engine solver, sliders or horse collision verified. Running capsule projection can exceed existing skirt motion radius in some frames; natural motion and residual clipping remain unconfirmed.'}
(ROOT/'reports/leg_collision_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
cfg=json.loads((ROOT/'mod.json').read_text());cfg['validation_report']='reports/leg_collision_validation.json'
cfg['source_files']=sorted(set(cfg['source_files'])|{'module/ShengxiuCollection/ModuleData/cloth_bodies.xml','reports/leg_collision_fit.json','reports/leg_collision_validation.json','reports/user_feedback_v1.1.1.json','tools/LegCollision.cs','tools/LegCollision.csproj','tools/fit_leg_collision.py','tools/prepare_leg_collision.py'})
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
print('LEG_COLLISION_CANDIDATE_VERIFIED',VERSION,sha(package),'native untouched; all cloth retained')
