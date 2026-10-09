"""Hair-only solver travel fit; preserve accepted skirt collision and geometry."""
import hashlib,json,shutil,subprocess,sys,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
import numpy as np
from cloth_payload import read,write,decode_positions
ROOT=Path(__file__).resolve().parents[1];WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
from cloth_compiler.validation import check_structure
policy=json.loads((ROOT/'tools/hair_clearance_policy.json').read_text());VERSION=policy['version']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
module=ROOT/'module/ShengxiuCollection';package=module/'AssetPackages/sx_mingyu.tpac'
BASE_SHA='78ba100f6fb9ff27a1699ce5ee5230bd827dec283271a5e0f0a1e77e3f469b16'
base=ROOT/'build/hair_clearance_baseline_v1.1.3';base.mkdir(exist_ok=True);baseline=base/'sx_mingyu.tpac'
if not baseline.exists():
 assert sha(package)==BASE_SHA
 shutil.copy2(package,baseline)
assert sha(baseline)==BASE_SHA
previous=json.loads((ROOT/'reports/back_collision_validation.json').read_text())
oldxml=base/'cloth_bodies.xml'
if not oldxml.exists():
 archive=ROOT/'dist/ShengxiuCollection_v1.1.3_Mod.zip'
 if not archive.exists():archive=ROOT/'dist/ShengxiuCollection_Mod.zip'
 with zipfile.ZipFile(archive) as z:raw=z.read('ShengxiuCollection/ModuleData/cloth_bodies.xml')
 assert hashlib.sha256(raw).hexdigest()==previous['collision_xml_sha256']
 oldxml.write_bytes(raw)
subprocess.run([sys.executable,str(ROOT/'tools/fit_back_collision.py'),f"--back-inset={policy['back_surface_inset_m']}",f"--top-height={policy['back_top_height_m']}",'--report','reports/hair_clearance_fit.json'],check=True)
xml=module/'ModuleData/cloth_bodies.xml';tree=ET.parse(xml).getroot()
def canon(b):return ET.canonicalize(ET.tostring(b,encoding='unicode'),strip_text=True)
assert canon(ET.parse(oldxml).getroot()[0])==canon(tree[0]),'Accepted leg collision changed'
caps=tree[1].findall('./capsules/capsule')
probe=ROOT/'build/cloth_probe/NativeClothProbe.dll';names=['sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs']
def inspect(p,dest):return json.loads(subprocess.check_output(['dotnet',str(probe),str(p),*names,'--dump-segments',str(dest)],encoding='utf-8'))
bd=ROOT/'build/hair_clearance_before_dump';ad=ROOT/'build/hair_clearance_after_dump'
before=inspect(baseline,bd)
head=next(mm for mm in before if mm['Name']=='sx_mingyu_head');mesh=next(m for m in head['meshes'] if m['Name']==policy['mesh'])
blobname=f"sx_mingyu_head_{mesh['Guid']}.bin";data=read(bd/blobname);old=read(bd/blobname)
rawskel=json.loads((ROOT/'reports/human_skeleton.json').read_text());rig=parse_skeljson(rawskel);lookup={b['name']:b['i'] for b in rawskel['bones']}
rest=decode_positions(data);weights=data['bone_weights'].reshape(-1,4)*255;bones=data['bone_indices'].reshape(-1,4)
active=data['max_distances']>0;required=np.zeros(len(rest));rows=[]
for label in ['idle','run']:
 anim=parse_animjson(json.loads((ROOT/f'reports/{label}.json').read_text()))
 frames=[max(1,anim['start'])] if label=='idle' else range(max(1,anim['start']),anim['frames'])
 for frame in frames:
  skin=skin_matrices(rig,anim,frame);p=lbs(rest,bones,weights,skin);moved=p.copy()
  for cap in caps:
   f=np.fromstring(cap.get('frame'),sep=',').reshape(4,4);ends=np.array([f[3,:3],f[3,:3]+f[0,:3]*float(cap.get('length'))])
   for i,point in enumerate(cap.findall('./points/point')):
    b=lookup[point.find('./bones/bone').get('name')];ends[i]=skin[b,:3,:3]@ends[i]+skin[b,:3,3]
   axis=ends[1]-ends[0];size=np.linalg.norm(axis);direction=axis/(size+.00001)
   t=np.clip((moved-ends[0])@direction,0,size);center=ends[0]+t[:,None]*direction
   delta=moved-center;length=np.linalg.norm(delta,axis=1);radius=float(cap.find('./points/point').get('radius'))
   moved=center+delta*(np.maximum(length,radius)/np.maximum(length,1e-12))[:,None]
  distance=np.linalg.norm(moved-p,axis=1);required=np.maximum(required,distance)
  rows.append({'animation':label,'frame':int(frame),'max_required_distance_m':float(distance[active].max()),'old_budget_conflict_positions':int((active&(distance>data['max_distances']+.0002)).sum())})
data['max_distances'][active]=np.maximum(data['max_distances'][active]*policy['minimum_existing_distance_scale'],required[active]+policy['projection_allowance_m'])
assert data['max_distances'].max()<=policy['maximum_solver_distance_m']
assert np.array_equal(data['max_distances']==0,old['max_distances']==0)
assert np.all(data['max_distances'][active]>=required[active]+.0049)
check_structure(data)
for key in old:
 if key in ['max_distances','offsets']:continue
 assert np.array_equal(data[key],old[key]),key
dest=ROOT/'build/hair_clearance_cooked';dest.mkdir(exist_ok=True);blob=dest/blobname;blob.write_bytes(write(data));assert write(read(blob))==blob.read_bytes()
manifest=dest/'manifest.json';manifest.write_text(json.dumps([{'metamesh':'sx_mingyu_head','guid':mesh['Guid'],'path':str(blob.resolve()),'sha256':sha(blob)}],indent=2))
candidate=ROOT/'build/hair_clearance_candidate_v1.1.4.tpac'
subprocess.run(['dotnet',str(ROOT/'build/cloth_patch/ClothPatch.dll'),str(baseline),str(manifest),str(candidate),'--allow-metameshes','sx_mingyu_head'],check=True)
after=inspect(candidate,ad)
PAYLOAD='b97e0f10-df49-4666-8f1d-ada6630d4b4e'
for a,b in zip(before,after):
 assert {k:v for k,v in a.items() if k!='segments'}=={k:v for k,v in b.items() if k!='segments'}
 keep=lambda mm:[s for s in mm['segments'] if not(s['TypeGuid']==PAYLOAD and s['OwnerGuid']==mesh['Guid'])]
 assert keep(a)==keep(b)
assert sha(ad/blobname)==sha(blob)
for p in bd.glob('*.bin'):
 if p.name!=blobname:assert sha(p)==sha(ad/p.name),p.name
audit=json.loads(subprocess.check_output([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(candidate),'--cloth-vertex-alpha'],encoding='utf-8'));assert audit['status']=='pass'
others={p.name:sha(p) for p in (module/'AssetPackages').glob('*.tpac') if p!=package};assert others==previous['other_set_package_hashes_unchanged']
shutil.copy2(candidate,package)
descriptor=ET.parse(module/'SubModule.xml');descriptor.find('Version').set('value',VERSION);ET.indent(descriptor,space='  ');descriptor.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
f=module/'SubModule.xml';f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
for row in previous['packages']:
 if row['prefix']=='sx_mingyu':row['sha256']=sha(package);row['report']='reports/hair_clearance_validation.json'
report={'status':'pass','version':VERSION,'check_scope':'offline_hair_solver_distance_candidate','final_package_sha256':sha(package),'baseline_package_sha256':BASE_SHA,'collision_xml_sha256':sha(xml),'accepted_leg_collision_unchanged':True,'all_56_mesh_metadata_and_geometry_hashes_identical':True,'all_fixed_roots_preserved':True,'all_editor_data_and_other_cloth_blobs_identical':True,'changed_blob_sha256':sha(blob),'only_hair_max_distances_changed':True,'old_max_solver_distance_m':float(old['max_distances'].max()),'new_max_solver_distance_m':float(data['max_distances'].max()),'offline_active_vertex_budget_conflicts_after':0,'motions':rows,'policy':policy,'other_set_package_hashes_unchanged':others,'packages':previous['packages'],'package_audit':audit,'game_test_verified':False,'limitations':'Native skeletal capsule projection only, not a full cloth solver. Larger hair travel and fitted back boundary require game confirmation of natural drape and back clipping; anchors, fabric constraints, body sliders and IK can still affect motion.'}
(ROOT/'reports/hair_clearance_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
cfg=json.loads((ROOT/'mod.json').read_text());cfg['validation_report']='reports/hair_clearance_validation.json'
cfg['source_files']=sorted(set(cfg['source_files'])|{'tools/hair_clearance_policy.json','tools/prepare_hair_clearance.py','reports/hair_clearance_fit.json','reports/hair_clearance_validation.json','reports/user_feedback_v1.1.3.json'})
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
print('HAIR_CLEARANCE_VERIFIED',VERSION,'max solver distance',data['max_distances'].max(),'old conflicts',max(r['old_budget_conflict_positions'] for r in rows),'new budget conflicts 0')
