"""Check final GPU bytes: only the authorized skirt alpha may change."""
from pathlib import Path
import sys,json,struct,hashlib,zipfile
import numpy as np
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));prefix=cfg['prefix'];ident=cfg['id'];B=R/'build'
def read_streams(path):
 data=path.read_bytes();offset=12;magic,version,count=struct.unpack_from('<III',data);rows={}
 def take(n):
  nonlocal offset
  value=data[offset:offset+n];offset+=n;return value
 def blob():return take(struct.unpack('<I',take(4))[0])
 for _ in range(count):
  name=blob().decode();lod=take(4);material=blob();guid=blob();n,ni=struct.unpack('<II',take(8));bbox=take(24);flags=struct.unpack('<I',take(4))[0];streams={}
  for field,size,enabled in [('positions',12,True),('normals',12,flags&1),('uv',8,True),('uv2',8,flags&2),('colors',4,flags&4),('colors2',4,flags&8),('tangents',16,flags&16),('bones',4,flags&32),('weights',4,True),('indices',4*ni//max(n,1),False)]:
   if enabled:streams[field]=take(n*size)
  streams['indices']=take(ni*4);rows[name]=dict(lod=lod,material=material,guid=guid,bbox=bbox,flags=flags,n=n,ni=ni,streams=streams)
 assert offset==len(data);return rows
allowed={r['object'] for r in json.loads((R/'build/manifest.json').read_text()) if r['material'] in cfg.get('calibrate_materials',[])};changes=[]
for lod in range(4):
 old={};new={}
 for p in (B/'baseline_v0.1.0_exports'/f'lod{lod}'/'geo').glob('*.bin'):old.update(read_streams(p))
 for p in (B/f'final_export_lod{lod}'/'geo').glob('*.bin'):new.update(read_streams(p))
 assert old.keys()==new.keys()
 for name in old:
  a=old[name];b=new[name];assert {k:v for k,v in a.items() if k!='streams'}=={k:v for k,v in b.items() if k!='streams'}
  for field,raw in a['streams'].items():
   current=b['streams'][field]
   if raw==current:continue
   assert field=='colors' and any(name.startswith(n) for n in allowed),(name,field)
   ac=np.frombuffer(raw,'u1').reshape(-1,4);bc=np.frombuffer(current,'u1').reshape(-1,4);assert np.array_equal(ac[:,:3],bc[:,:3]);assert np.array_equal(ac[:,3]==0,bc[:,3]==0)
   changes.append(dict(mesh=name,lod=lod,changed_alpha_vertices=int((ac[:,3]!=bc[:,3]).sum()),fixed_roots_unchanged=True))
base=B/'baseline_v0.1.0_exports/lod0';current=B/'final_export_lod0';oldpack=json.loads((base/'pack.json').read_text());newpack=json.loads((current/'pack.json').read_text());assert oldpack['materials']==newpack['materials'] and oldpack['skeletons']==newpack['skeletons']
for texture in oldpack['textures']:assert (base/texture['file']).read_bytes()==(current/texture['file']).read_bytes()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pkg=R/'module'/ident/'AssetPackages'/(prefix+'.tpac')
if not allowed:assert sha(pkg)==cfg['baseline_package_sha256']
# The compiled preview adapter is deliberately preserved from the accepted release.
archive_path=R/'dist'/(ident+'_v0.1.0_Mod.zip')
if not archive_path.exists():archive_path=R/'dist'/(ident+'_Mod.zip')
with zipfile.ZipFile(archive_path) as archive:
 dll=R/'module'/ident/'bin/Win64_Shipping_Client'/(ident+'.UIRuntime.dll');assert archive.read(ident+'/bin/Win64_Shipping_Client/'+dll.name)==dll.read_bytes()
oldcloth={json.loads(p.read_text())['name']:p for p in (B/'baseline_cloth').glob('*.mesh.json')};newcloth={json.loads(p.read_text())['name']:p for p in (B/'cloth_final').glob('*.mesh.json')};assert oldcloth and oldcloth.keys()==newcloth.keys();preserved_cloth=0
for name,path in oldcloth.items():
 if any(name.startswith(n) for n in allowed):continue
 blob=lambda p:p.with_name(p.name.removesuffix('.mesh.json')+'.bin')
 assert blob(path).read_bytes()==blob(newcloth[name]).read_bytes(),('Non-target cloth payload changed',name)
 preserved_cloth+=1
report=dict(non_target_cloth_payloads_byte_identical=preserved_cloth,status='pass',version=cfg['version'],baseline_version='v0.1.0',baseline_package_sha256=cfg['baseline_package_sha256'],final_package_sha256=sha(pkg),geometry_normals_uv_tangents_weights_indices_preserved=True,materials_textures_skeleton_preserved=True,ui_runtime_unchanged=True,alpha_changes=changes,game_verified=False)
(R/'reports/skirt_preservation_validation.json').write_text(json.dumps(report,indent=2));print('SKIRT_PRESERVATION_VERIFIED',ident,changes)
