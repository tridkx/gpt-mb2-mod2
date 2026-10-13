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
for lod in range(4):
 folder=B/f'trial_baseline_lod{lod}'
 subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(baseline),str(folder),str(lod)],check=True,stdout=subprocess.DEVNULL)
 old={}
 for path in (folder/'geo').glob('*.bin'):old.update(read_streams(path))
 for g in json.loads((B/'geometry.json').read_text()):
  if g['lod']!=lod or g.get('cloth'):continue
  path=Path(g['geometry']);blob=bytearray(path.read_bytes());nv=np.frombuffer(blob,'<i4',3)[1];a=old[g['name']]
  assert a['n']==nv and a['streams']['positions']==blob[12:12+nv*12]
  offset=12+nv*56;blob[offset:offset+nv*4]=a['streams']['colors'];path.write_bytes(blob)
print('NON_TARGET_VERTEX_COLORS_PRESERVED')
