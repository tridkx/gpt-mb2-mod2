"""Fast pre-build rejection of pose fit that tears or folds the source panels."""
import sys,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project_paths import resolve_project
import numpy as np
from scipy.spatial import cKDTree
WS=Path(__file__).resolve().parents[1];ROOT=resolve_project(WS,sys.argv[1]);BASE=ROOT/'build/repair_baseline_v1.0.0'
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'));sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
a=np.load(ROOT/'build/skirt_clearance_fit.npz');old=np.load(BASE/'rig_arrays.npz');name=str(a['object'])
from subprocess import run
folder=BASE/'export/geo'
if not folder.exists():run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(BASE/json.loads((ROOT/'mod.json').read_text())['package']),str(BASE/'export'),'0'],check=True,capture_output=True)
m=next(m for f in folder.glob('*.bin') for m in read_geo(f) if m['name']==name);_,vi=cKDTree(old[name+'_P']).query(m['pos']);tri=vi[m['idx'].reshape(-1,3)]
tri=np.array(json.loads((ROOT/'build/skirt_triangles.json').read_text()))
edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);u,v=edges.T;p=a['P'];length=np.linalg.norm(p[u]-p[v],axis=1);valid=length>.003
w=a['W'];bi=np.argsort(-w,axis=1)[:,:4];bw=np.take_along_axis(w,bi,axis=1)*255
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));result=[]
for label in ['idle','run','bow','riding']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));frames=list(range(max(1,anim['start']),anim['frames'])) if label!='idle' else sorted(set(np.linspace(1,anim['frames']-1,16).astype(int).tolist()))
    maximum=0;p99=0;frame=0
    for f in frames:
        posed=lbs(p,bi,bw,skin_matrices(rig,anim,f));r=np.linalg.norm(posed[u[valid]]-posed[v[valid]],axis=1)/length[valid]
        if r.max()>maximum:maximum=float(r.max());frame=f;worst_edge=int(np.argmax(r))
        p99=max(p99,float(np.quantile(r,.99)))
    indices=np.where(valid)[0][worst_edge];pair=[int(u[indices]),int(v[indices])]
    result.append({'label':label,'max':maximum,'p99':p99,'frame':frame,'edge':pair,'rest_length':float(length[indices]),'weights':w[pair].tolist(),'position':p[pair].tolist()})
print(json.dumps(result,indent=2));(ROOT/'build/skirt_fit_deformation.json').write_text(json.dumps(result,indent=2))
