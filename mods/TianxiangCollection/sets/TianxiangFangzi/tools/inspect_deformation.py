import sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'));sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
m=next(m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f) if m['name']=='fz5_body_08');rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));anim=parse_animjson(json.loads((ROOT/'reports/bow.json').read_text()));q=lbs(m['pos'],m['bi'],m['bw'],skin_matrices(rig,anim,1));t=m['idx'].reshape(-1,3);e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);u,v=e.T;l=np.linalg.norm(m['pos'][u]-m['pos'][v],axis=1);r=np.linalg.norm(q[u]-q[v],axis=1)/np.maximum(l,1e-9);r[l<.003]=0
for i in np.argsort(-r)[:5]:
    ids=e[i];print('EDGE',r[i],l[i],m['pos'][ids].tolist(),m['bi'][ids].tolist(),m['bw'][ids].tolist())
