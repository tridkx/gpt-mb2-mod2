"""Evidence from actual vanilla tassels; preserve every existing geometry byte."""
from pathlib import Path
import json,subprocess,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
NATIVE=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
BASE=ROOT/'build/cloth_baseline_v1.0.3'
PACKAGE=ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
PROBE=ROOT/'build/cloth_probe/NativeClothProbe.dll'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def probe(package,names):
 return json.loads(subprocess.check_output(['dotnet',str(PROBE),str(package),*names],text=True,encoding='utf-8'))
native_package=NATIVE/'EmAssetPackages/crafting/crafting.tpac'
native=probe(native_package,['spear_blade_19','spear_banner_16','spear_banner_17'])
(ROOT/'reports/native_glaive_cloth.json').write_text(json.dumps(native,indent=2))
weapon_file=NATIVE.parent/'SandBoxCore/ModuleData/items/weapons.xml'
weapon=next(x for x in ET.parse(weapon_file).getroot() if x.get('id')=='khuzait_polearm_1_t4')
pieces=[dict(p.attrib) for p in weapon.findall('./Pieces/Piece')]
assert any(p['id']=='spear_banner_16' and p['Type']=='Guard' for p in pieces)
reference=next(m for mm in native if mm['Name']=='spear_banner_16' for m in mm['meshes'] if m['Lod']==0)
assert reference['Flags']==['uses_cloth_simulation','force_enable_cloth'] and reference['UnknownBool3']
assert reference['alpha_min']==0 and reference['alpha_max']==255 and reference['SkinDataSize']==0
old=probe(BASE/'sx_mingyu.tpac',['sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs'])
new=probe(PACKAGE,['sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs'])
changed=[];preserved=[]
for mm in new:
 previous=next(x for x in old if x['Name']==mm['Name'])
 assert {k:v for k,v in mm.items() if k not in ['meshes','segments']}=={k:v for k,v in previous.items() if k not in ['meshes','segments']}
 for m in mm['meshes']:
  before=next(x for x in previous['meshes'] if x['Name']==m['Name'])
  assert m['geometry_hash']==before['geometry_hash']
  if 'uses_cloth_simulation' in before['Flags']:
   assert m['Flags']==reference['Flags'] and m['UnknownBool3']==reference['UnknownBool3']
   assert {k:v for k,v in m.items() if k!='edit_bones'}=={k:v for k,v in before.items() if k!='edit_bones'}
   assert m['edit_bones']==m['edit_positions']
   changed.append(m['Name'])
  else:assert m==before
  preserved.append(m['Name'])
assert len(changed)==4 and len(preserved)==56
for file in ['ShengxiuCollection_Rigged.blend','ShengxiuCollection_Rigged.fbx']:
 assert sha(ROOT/'source'/file)==sha(BASE/file)
from verify_cooked_cloth import verify
verify(PACKAGE)
report={'status':'pass','version':'v1.0.4','final_package_sha256':sha(PACKAGE),'baseline_package_sha256':sha(BASE/'sx_mingyu.tpac'),
 'native_package':str(native_package),'native_package_sha256':sha(native_package),'weapon_id':weapon.get('id'),'weapon_pieces':pieces,
 'native_reference':reference,'changed_meshes':changed,'all_56_geometry_streams_and_indices_identical':True,
 'all_cloth_parameters_and_alpha_identical_to_v1_0_2':True,'editable_blend_and_fbx_identical':True,
 'changes':['add four own generated cloth payloads','fill editor skin data for four cloth meshes','add explicit solver-only roots for previously unanchored ornaments and hair strands'],
 'interpretation':'Native payload layout verified across seven byte-exact roundtrips; own triangle cloth network verified offline. Engine acceptance and dynamics remain unverified.',
 'game_solver_verified':False}
(ROOT/'reports/cloth_activation_validation.json').write_text(json.dumps(report,indent=2))
print('NATIVE_TASSEL_ACTIVATION_ALIGNED; 56 GEOMETRY STREAMS IDENTICAL')
