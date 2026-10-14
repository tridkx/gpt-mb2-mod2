"""Compare pure skinning layer crossings, using identical source poses."""
import sys,json,textwrap
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
# Keep the already-used intersection criterion: deep (>1 mm) crossings only.
def edge_hits(a,b):
    found=np.zeros(len(a),bool);e1=b[:,1]-b[:,0];e2=b[:,2]-b[:,0]
    for j in range(3):
        start=a[:,j];direction=a[:,(j+1)%3]-start;h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);good=abs(det)>1e-12;reciprocal=np.zeros(len(a));reciprocal[good]=1/det[good];s=start-b[:,0];u=np.einsum('ij,ij->i',s,h)*reciprocal;q=np.cross(s,e1);v=np.einsum('ij,ij->i',direction,q)*reciprocal;t=np.einsum('ij,ij->i',e2,q)*reciprocal;margin=.001/np.maximum(np.linalg.norm(direction,axis=1),1e-12);found|=good&(u>1e-5)&(v>1e-5)&(u+v<1-1e-5)&(t>margin)&(t<1-margin)
    return found
def crossings(p,groups):
    keys=list(groups);trees={k:BVHTree.FromPolygons(p.tolist(),groups[k].tolist(),all_triangles=True) for k in keys};total=0
    for j,a in enumerate(keys):
        for b in keys[j+1:]:
            pairs=np.array(trees[a].overlap(trees[b]),int)
            if not len(pairs):continue
            ta=p[groups[a][pairs[:,0]]];tb=p[groups[b][pairs[:,1]]];na=np.cross(ta[:,1]-ta[:,0],ta[:,2]-ta[:,0]);nb=np.cross(tb[:,1]-tb[:,0],tb[:,2]-tb[:,0]);na/=np.maximum(np.linalg.norm(na,axis=1)[:,None],1e-12);nb/=np.maximum(np.linalg.norm(nb,axis=1)[:,None],1e-12);da=np.einsum('nvc,nc->nv',ta-tb[:,0,None,:],nb);db=np.einsum('nvc,nc->nv',tb-ta[:,0,None,:],na);deep=((da.min(1)<-.001)&(da.max(1)>.001))|((db.min(1)<-.001)&(db.max(1)>.001));total+=int((deep&(edge_hits(ta,tb)|edge_hits(tb,ta))).sum())
    return total
old=np.load(R/'build/sleeve_skin_baseline_v0.1.1.npz');new=np.load(R/'build/fitted_model.npz');p=old['bql_part_13_p'];f=old['bql_part_13_f'];q,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);parent=np.arange(len(q))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for a,b in np.concatenate([inv[f][:,[0,1]],inv[f][:,[1,2]],inv[f][:,[2,0]]]):
 a,b=root(a),root(b)
 if a!=b:parent[max(a,b)]=min(a,b)
_,labels=np.unique([root(i) for i in range(len(q))],return_inverse=True);labels=labels[inv];groups={c:f[(labels[f]==c).all(1)] for c in set(labels) if (labels==c).sum()>=100};assert len(groups)==6
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));results=[]
all_crossings=crossings
left={k:f for k,f in groups.items() if p[f].mean(axis=(0,1))[0]<0};right={k:f for k,f in groups.items() if p[f].mean(axis=(0,1))[0]>0}
def crossings(points,unused):return all_crossings(points,left)+all_crossings(points,right)
def quantize(w):
 bi=np.argsort(-w,axis=1,kind='stable')[:,:4];v=np.take_along_axis(w,bi,axis=1);v/=v.sum(1)[:,None];bw=np.floor(v*255).astype(int);bw[:,0]+=255-bw.sum(1);return bi,bw
old_b,old_w=quantize(old['bql_part_13_w']);new_b,new_w=quantize(new['bql_part_13_w'])
for name in ['ui_neutral_female','run','bow','riding']:
 a=parse_animjson(json.loads((R/'reports'/(name+'.json')).read_text()));frames=np.unique(np.linspace(max(1,a['start']),min(a['frames']-1,121) if name=='ui_neutral_female' else a['frames']-1,12).astype(int));before=[];after=[]
 for frame in frames:
  matrices=skin_matrices(rig,a,int(frame));before.append(crossings(lbs(p,old_b,old_w,matrices),groups));after.append(crossings(lbs(p,new_b,new_w,matrices),groups))
 row=dict(motion=name,source_frames=frames.tolist(),old_mean=float(np.mean(before)),new_mean=float(np.mean(after)),old_max=max(before),new_max=max(after));results.append(row);print('SKIN_CROSSINGS',row,flush=True)
(R/'reports/sleeve_skinning_motion.json').write_text(json.dumps(dict(scope='Three principal layers per side; same-side intersections only; 12 source poses per action, quantized pure skinning; not game proof',game_verified=False,opposite_sleeve_and_body_collision_not_tested=True,results=results),indent=2))
