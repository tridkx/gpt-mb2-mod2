"""Compose v1.1.3 hair/back collision candidate; retain accepted skirt fix."""
import hashlib,json,shutil,subprocess,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];VERSION='v1.1.3'
BASE_SHA='1bed45f0e763815e7cd3dd6f0b74e19cdc843730f8a26f9a2221a4952fc9d649'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
module=ROOT/'module/ShengxiuCollection';package=module/'AssetPackages/sx_mingyu.tpac'
base=ROOT/'build/back_collision_baseline_v1.1.2';base.mkdir(exist_ok=True)
baseline=base/'sx_mingyu.tpac';baseline_xml=base/'cloth_bodies.xml'
if not baseline.exists():
 assert sha(package)==BASE_SHA
 shutil.copy2(package,baseline)
assert sha(baseline)==BASE_SHA
previous=json.loads((ROOT/'reports/leg_collision_validation.json').read_text())
if not baseline_xml.exists():
 archive=ROOT/'dist/ShengxiuCollection_v1.1.2_Mod.zip'
 if not archive.exists():archive=ROOT/'dist/ShengxiuCollection_Mod.zip'
 with zipfile.ZipFile(archive) as z:
  raw=z.read('ShengxiuCollection/ModuleData/cloth_bodies.xml')
 assert hashlib.sha256(raw).hexdigest()==previous['collision_xml_sha256']
 baseline_xml.write_bytes(raw)
assert sha(baseline_xml)==previous['collision_xml_sha256']
fit=json.loads((ROOT/'reports/back_collision_fit.json').read_text());assert fit['status']=='pass'
xml=module/'ModuleData/cloth_bodies.xml';assert sha(xml)==fit['xml_sha256']
before_xml=ET.parse(baseline_xml).getroot();after_xml=ET.parse(xml).getroot()
assert len(before_xml)==1 and len(after_xml)==2
def canon(b):return ET.canonicalize(ET.tostring(b,encoding='unicode'),strip_text=True)
leg=next(b for b in after_xml if b.get('name')=='sx_mingyu_leg_collision')
assert canon(before_xml[0])==canon(leg),'Accepted leg collision changed'
back=next(b for b in after_xml if b.get('name')=='sx_mingyu_back_collision')
assert len(back.findall('./capsules/capsule'))==3
assert back.get('owner_skeleton')=='human_skeleton'
assert fit['hair_projection_diagnostics'][0]['max_lift_m']<.006
native=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/ModuleData/cloth_bodies.xml')
assert sha(native)==json.loads((ROOT/'reports/leg_collision_fit.json').read_text())['native_cloth_bodies_sha256']
candidate=ROOT/'build/back_collision_candidate_v1.1.3.tpac'
subprocess.run(['dotnet',str(ROOT/'build/back_collision/BackCollision.dll'),str(baseline),str(candidate)],check=True)
probe=ROOT/'build/cloth_probe/NativeClothProbe.dll';names=['sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs']
def inspect(p,dest):return json.loads(subprocess.check_output(['dotnet',str(probe),str(p),*names,'--dump-segments',str(dest)],encoding='utf-8'))
bd=ROOT/'build/back_collision_before_dump';ad=ROOT/'build/back_collision_after_dump'
before=inspect(baseline,bd);after=inspect(candidate,ad)
for old,new in zip(before,after):
 expected=dict(old)
 if old['Name']=='sx_mingyu_head':expected['body']=back.get('name')
 assert expected==new,(old['Name'],'Unexpected change')
blobs={p.name:sha(p) for p in bd.glob('*.bin')};assert len(blobs)==8
assert blobs=={p.name:sha(p) for p in ad.glob('*.bin')}
assert sum('uses_cloth_simulation' in m['Flags'] for mm in after for m in mm['meshes'])==4
audit=json.loads(subprocess.check_output([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(candidate),'--cloth-vertex-alpha'],encoding='utf-8'))
assert audit['status']=='pass'
others={p.name:sha(p) for p in (module/'AssetPackages').glob('*.tpac') if p!=package}
assert others==previous['other_set_package_hashes_unchanged']
shutil.copy2(candidate,package)
descriptor=ET.parse(module/'SubModule.xml');descriptor.find('Version').set('value',VERSION)
ET.indent(descriptor,space='  ');descriptor.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
f=module/'SubModule.xml';f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
assert len(ET.parse(module/'ModuleData/items.xml').getroot())==9
for row in previous['packages']:
 if row['prefix']=='sx_mingyu':row['sha256']=sha(package);row['report']='reports/back_collision_validation.json'
report={'status':'pass','version':VERSION,'check_scope':'offline_hair_back_collision_candidate','final_package_sha256':sha(package),'baseline_package_sha256':BASE_SHA,'own_hair_back_collision_body':back.get('name'),'collision_xml_sha256':sha(xml),'accepted_leg_body_canonical_xml_unchanged':True,'native_cloth_bodies_preserved':True,'all_56_mesh_metadata_and_geometry_hashes_identical':True,'all_metamesh_segment_checksums_identical':True,'cloth_and_editor_blob_sha256':blobs,'all_four_cloth_payloads_and_parameters_identical':True,'other_set_package_hashes_unchanged':others,'packages':previous['packages'],'back_fit_report':'reports/back_collision_fit.json','registered_items':9,'package_audit':audit,'game_test_verified':False,'limitations':'Hair-only posterior torso collider with three vertical capsules; does not restore native full human_body. No engine cloth, dummy collision, sliders or horse collision verified. Some projected hair points exceed existing 25mm travel budget. User must confirm running back clearance and unchanged natural drape; skirt fix is user-confirmed for v1.1.2 only.'}
(ROOT/'reports/back_collision_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
cfg=json.loads((ROOT/'mod.json').read_text());cfg['validation_report']='reports/back_collision_validation.json'
cfg['source_files']=sorted(set(cfg['source_files'])|{'reports/back_collision_fit.json','reports/back_collision_validation.json','reports/user_feedback_v1.1.2.json','tools/BackCollision.cs','tools/BackCollision.csproj','tools/fit_back_collision.py','tools/prepare_back_collision.py'})
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
print('BACK_COLLISION_CANDIDATE_VERIFIED',VERSION,sha(package),'skirt collider and all cloth preserved')
