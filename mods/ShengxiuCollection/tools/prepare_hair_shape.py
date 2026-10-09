"""Build hair-only candidate; all accepted body geometry/cloth stays intact."""
import json,shutil,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parents[1];BUILD=ROOT/'build'
sys.path.insert(0,str(WS/'tools'))
from cloth_compiler.cook_cloth import cook
from cloth_compiler.cloth_payload import read,write
from cloth_compiler.validation import check_structure
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
package=ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
base=BUILD/'hair_shape_baseline_v1.1.4';base.mkdir(exist_ok=True);baseline=base/'sx_mingyu.tpac'
if not baseline.exists():shutil.copy2(package,baseline)
assert sha(baseline)=='4e4e921944451b8612471426177159d8f1ee1ec96a35b9a1892e541edeb3a0ef'
spec=json.loads((BUILD/'spec.json').read_text());spec['output']=str(BUILD/'hair_shape_donor.tpac')
geometry=json.loads((BUILD/'geometry.json').read_text())
for part in spec['meshes']:
 for group in part['groups']:
  group['geometry']=next(g['geometry'] for g in geometry if g['name']==group['name'])
(BUILD/'hair_shape_spec.json').write_text(json.dumps(spec,indent=2))
subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','build',str(BUILD/'hair_shape_spec.json')],check=True,stdout=subprocess.DEVNULL)
uncooked=BUILD/'hair_shape_uncooked.tpac'
subprocess.run(['dotnet',str(BUILD/'hair_geometry/HairGeometry.dll'),str(baseline),spec['output'],str(uncooked)],check=True)
dump=BUILD/'hair_shape_cook_input';probe=BUILD/'cloth_probe/NativeClothProbe.dll'
before=json.loads(subprocess.check_output(['dotnet',str(probe),str(baseline),'sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs','--dump-segments',str(base/'dump')]))
subprocess.run(['dotnet',str(probe),str(uncooked),'sx_mingyu_head','--dump-segments',str(dump)],check=True,stdout=subprocess.DEVNULL)
mesh=next(json.loads(p.read_text()) for p in dump.glob('*.mesh.json') if json.loads(p.read_text())['name']=='sx_mingyu_head_00')
policy=json.loads((ROOT/'tools/cloth_policy.json').read_text())['meshes'][mesh['name']]
raw,row=cook(mesh,policy);check_structure(read(raw));assert write(read(raw))==raw
dest=BUILD/'hair_shape_cooked';dest.mkdir(exist_ok=True);blob=dest/(mesh['guid']+'.bin');blob.write_bytes(raw);row['path']=str(blob.resolve())
(dest/'manifest.json').write_text(json.dumps([row],indent=2))
candidate=BUILD/'hair_shape_candidate_v1.1.5.tpac'
subprocess.run(['dotnet',str(BUILD/'cloth_patch/ClothPatch.dll'),str(uncooked),str(dest/'manifest.json'),str(candidate),'--allow-metameshes','sx_mingyu_head'],check=True)
after=json.loads(subprocess.check_output(['dotnet',str(probe),str(candidate),'sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs','--dump-segments',str(BUILD/'hair_shape_final_dump')]))
changed=[]
for a,b in zip(before,after):
 assert {k:v for k,v in a.items() if k not in ['meshes','segments']}=={k:v for k,v in b.items() if k not in ['meshes','segments']}
 for old,new in zip(a['meshes'],b['meshes']):
  if old==new:continue
  assert old['Name']=='sx_mingyu_head_00' or old['Name'].startswith('sx_mingyu_head_00.lod'),old['Name']
  assert old['Guid']==new['Guid'] and old['Flags']==new['Flags'] and old['ClothingMaterial']==new['ClothingMaterial']
  changed.append(old['Name'])
assert len(changed)==4
for p in (base/'dump').glob('*.bin'):
 if p.name.startswith('sx_mingyu_head_'):continue
 assert sha(p)==sha(BUILD/'hair_shape_final_dump'/p.name),p.name
audit=json.loads(subprocess.check_output([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(candidate),'--cloth-vertex-alpha']))
assert audit['status']=='pass'
(ROOT/'reports/hair_shape_build.json').write_text(json.dumps({'status':'pass','baseline_package_sha256':sha(baseline),'candidate_sha256':sha(candidate),'changed_meshes':changed,'other_52_meshes_identical':True,'accepted_body_cloth_and_editor_segments_identical':True,'cloth_cook':row,'package_audit':audit},indent=2))
for lod in range(4):
 dest=BUILD/('hair_shape_final_export'+('' if lod==0 else '_lod'+str(lod)))
 subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(candidate),str(dest),str(lod),'--all-mips'],check=True,stdout=subprocess.DEVNULL)
print('HAIR_SHAPE_BUILT',sha(candidate))
