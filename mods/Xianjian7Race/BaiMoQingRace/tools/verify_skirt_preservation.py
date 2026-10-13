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

import subprocess
baseline=B/'trial_baseline_v0.1.2.tpac'
with zipfile.ZipFile(R/'dist/BaiMoQingRace_v0.1.2_Mod.zip') as z:baseline.write_bytes(z.read('BaiMoQingRace/AssetPackages/bmq.tpac'))
changes=[]
for lod in range(4):
 folder=B/f'trial_baseline_lod{lod}'
 subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(baseline),str(folder),str(lod)]+(['--all-mips'] if lod==0 else []),check=True,stdout=subprocess.DEVNULL)
 old={};new={}
 for path in (folder/'geo').glob('*.bin'):old.update(read_streams(path))
 for path in (B/f'final_export_lod{lod}'/'geo').glob('*.bin'):new.update(read_streams(path))
 assert old.keys()==new.keys()
 for name,a in old.items():
  b=new[name]
  assert {k:v for k,v in a.items() if k!='streams'}=={k:v for k,v in b.items() if k!='streams'},name
  for field,raw in a['streams'].items():
   current=b['streams'][field]
   if raw==current:continue
   assert field=='colors' and name.startswith(('bmq_part_00','bmq_part_01')),(name,field)
   ac=np.frombuffer(raw,'u1').reshape(-1,4);bc=np.frombuffer(current,'u1').reshape(-1,4)
   assert np.array_equal(ac[:,:3],bc[:,:3])
   changes.append(dict(mesh=name,lod=lod,changed_alpha_vertices=int((ac[:,3]!=bc[:,3]).sum())))
 if lod==0:
  oldpack=json.loads((folder/'pack.json').read_text());newpack=json.loads((B/'final_export_lod0/pack.json').read_text())
  assert oldpack['materials']==newpack['materials'] and oldpack['skeletons']==newpack['skeletons']
  for t in oldpack['textures']:assert (folder/t['file']).read_bytes()==(B/'final_export_lod0'/t['file']).read_bytes()
with zipfile.ZipFile(R/'dist/BaiMoQingRace_v0.1.2_Mod.zip') as z:
 dll=R/'module/BaiMoQingRace/bin/Win64_Shipping_Client/BaiMoQingRace.UIRuntime.dll'
 assert z.read('BaiMoQingRace/bin/Win64_Shipping_Client/'+dll.name)==dll.read_bytes()
report=dict(status='pass',version=cfg['version'],baseline_version='v0.1.2',final_package_sha256=hashlib.sha256((R/'module/BaiMoQingRace/AssetPackages/bmq.tpac').read_bytes()).hexdigest(),geometry_normals_uv_tangents_weights_indices_preserved=True,materials_textures_skeleton_preserved=True,ui_runtime_unchanged=True,only_skirt_alpha_changed=changes,game_verified=False)
(R/'reports/skirt_preservation_validation.json').write_text(json.dumps(report,indent=2));print(report)
