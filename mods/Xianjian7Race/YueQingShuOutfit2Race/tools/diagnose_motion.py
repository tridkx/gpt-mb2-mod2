"""Locate final byte-weight edges responsible for native-motion tears."""
from pathlib import Path
import sys,json,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1];WS=workspace_root(R)
sys.path[:0]=[str(WS/'tools/asset_helpers/tools'),str(WS/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
failure=json.loads((R/'reports/motion_failure.json').read_text());rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));anim=parse_animjson(json.loads((R/'reports'/(failure['label']+'.json')).read_text()));skin=skin_matrices(rig,anim,failure['frame'])
meshes=[m for p in (R/'build/final_export_lod0/geo').glob('*.bin') for m in read_geo(p) if m['name']==failure['mesh']]
for m in meshes:
 f=m['idx'].reshape(-1,3);e=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0);base=np.linalg.norm(m['pos'][e[:,0]]-m['pos'][e[:,1]],axis=1);e=e[base>.002];base=base[base>.002];p=lbs(m['pos'],m['bi'],m['bw'],skin);ratio=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)/base
 print(R.name,failure['label'],failure['frame'])
 for i in np.argsort(ratio)[-8:]:
  print('ratio',ratio[i],'length',base[i])
  for v in e[i]:print(np.round(m['pos'][v],4),[(rig['names'][int(b)],int(w)) for b,w in zip(m['bi'][v],m['bw'][v]) if w])
