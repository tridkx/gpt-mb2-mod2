"""Locate actual severe stretch in final native bow frames."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'));sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
anim=parse_animjson(json.loads((ROOT/'reports/bow.json').read_text()))
meshes=[m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f)]
for m in meshes:
 p=lbs(m['pos'],m['bi'],m['bw'],skin_matrices(rig,anim,54));tri=m['idx'].reshape(-1,3)
 edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);a,b=edges.T
 length=np.linalg.norm(m['pos'][a]-m['pos'][b],axis=1);valid=length>.003
 ratio=np.linalg.norm(p[a[valid]]-p[b[valid]],axis=1)/length[valid]
 if ratio.max()<3:continue
 print('MESH',m['name'],'MAX',ratio.max())
 bad=edges[valid][np.argsort(-ratio)[:4]]
 for u,v in bad:
  print('EDGE',u,v,'rest',m['pos'][[u,v]].tolist(),'bi',m['bi'][[u,v]].tolist(),'bw',m['bw'][[u,v]].tolist())
