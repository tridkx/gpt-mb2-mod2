import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/tools'));sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
root=Path(__file__).resolve().parents[1]
s=next(s for f in (root/'build/final_export/geo').glob('*.bin') for s in read_geo(f) if s['name']=='tx5_body_03')
rig=parse_skeljson(json.load(open(root/'reports/human_skeleton.json')))
anim=parse_animjson(json.load(open(root/'reports/run.json')))
tri=s['idx'].reshape(-1,3);e=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);rest=np.linalg.norm(s['pos'][e[:,0]]-s['pos'][e[:,1]],axis=1)
p=lbs(s['pos'],s['bi'],s['bw'],skin_matrices(rig,anim,18));now=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1);ratio=now/np.maximum(rest,.005)
for k in np.argsort(-ratio)[:8]:
 print('ratio',round(ratio[k],2),'rest',round(rest[k],4),'vertices',e[k].tolist(),'position',np.round(s['pos'][e[k]],3).tolist(),'BI',s['bi'][e[k]].tolist(),'BW',s['bw'][e[k]].tolist())
