"""Locate excessive final-package motion edges in source coordinates."""
from pathlib import Path
import sys,json,numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[1]
sys.path[:0]=[str(WORKSPACE/'tools/asset_helpers/tools'),str(WORKSPACE/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
r=ROOT/'sets'/sys.argv[1];mesh=sys.argv[2];label=sys.argv[3];frame=int(sys.argv[4])
m=next(m for f in (r/'build/final_export/geo').glob('*.bin') for m in read_geo(f) if m['name']==mesh);arrays=np.load(r/'build/rig_arrays.npz')
t=m['idx'].reshape(-1,3);e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);u,v=e.T;l=np.linalg.norm(m['pos'][u]-m['pos'][v],axis=1)
sk=skin_matrices(parse_skeljson(json.loads((r/'reports/human_skeleton.json').read_text())),parse_animjson(json.loads((r/'reports'/(label+'.json')).read_text())),frame)
p=lbs(m['pos'],m['bi'],m['bw'],sk);rat=np.linalg.norm(p[u]-p[v],axis=1)/np.maximum(l,1e-9);rat[l<=.003]=0;tree=cKDTree(arrays[mesh+'_P'])
for i in np.argsort(-rat)[:6]:
 print('ratio',float(rat[i]),'length',float(l[i]))
 for k in [u[i],v[i]]:
  _,idx=tree.query(m['pos'][k]);print('source',arrays[mesh+'_S'][idx],'bones',m['bi'][k],m['bw'][k])
