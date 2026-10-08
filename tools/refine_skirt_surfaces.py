"""Refine a pose fit against the actual leg meshes, rather than capsules."""
import bpy,sys,json
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[sys.argv.index('--')+1];BASE=ROOT/'build/repair_baseline_v1.0.0'
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'));sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
f=np.load(ROOT/'build/skirt_clearance_fit.npz');q=f['P'].copy();w=f['W'];name=str(f['object']);old=np.load(BASE/'rig_arrays.npz');original=old[name+'_P']
meshes=[m for path in (BASE/'export/geo').glob('*.bin') for m in read_geo(path)]
m=next(m for m in meshes if m['name']==name);kd=KDTree(len(original))
for i,p in enumerate(original):kd.insert(p,i)
kd.balance();mapping=np.array([kd.find(p)[1] for p in m['pos']]);tri=mapping[m['idx'].reshape(-1,3)]
tri=np.array(json.loads((ROOT/'build/skirt_triangles.json').read_text()))
parts=json.loads((BASE/'reports/rig_fit.json').read_text())['parts'];names={r['object'] for r in parts if r['part']=='legs'};body=[m for m in meshes if m['name'] in names]
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));samples=[]
for label in ['run','bow','riding','idle']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));frames=range(max(1,anim['start']),anim['frames']) if label!='idle' else sorted(set(np.linspace(1,anim['frames']-1,16).astype(int)))
    for frame in frames:
        sk=skin_matrices(rig,anim,frame);pts=[];faces=[];off=0
        for m in body:
            p=lbs(m['pos'],m['bi'],m['bw'],sk);pts.extend(p.tolist());faces.extend((m['idx'].reshape(-1,3)+off).tolist());off+=len(p)
        tree=BVHTree.FromPolygons(pts,faces,all_triangles=True,epsilon=0)
        A=np.einsum('nb,bij->nij',w,sk[:,:3,:3]);t=w@sk[:,:3,3];samples.append((label,frame,A,t,np.linalg.pinv(A),tree))
edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);u,v=edges.T;n=len(q);length0=np.linalg.norm(original[u]-original[v],axis=1);degree=np.bincount(np.r_[u,v],minlength=n)
history=[]
for iteration in range(40):
    delta=np.zeros_like(q);count=np.zeros(n);totals={};maximum={}
    for label,frame,A,t,inv,bodytree in samples:
        posed=np.einsum('nij,nj->ni',A,q)+t;tree=BVHTree.FromPolygons(posed.tolist(),tri.tolist(),all_triangles=True,epsilon=0);hits=tree.overlap(bodytree)
        totals[label]=totals.get(label,0)+len(hits);maximum[label]=max(maximum.get(label,0),len(hits))
        for fi in sorted({h[0] for h in hits}):
            ids=tri[fi];center=posed[ids].mean(0);nearest,normal,_,distance=bodytree.find_nearest(center);normal=np.array(normal);nearest=np.array(nearest)
            # Correct the penetrating side of each actual intersecting triangle.
            signed=(posed[ids]-nearest)@normal;amount=np.maximum(.006-signed,0)
            if amount.max()<.001:amount[:]=.006
            correction=normal[None,:]*np.minimum(amount,.015)[:,None]
            np.add.at(delta,ids,np.einsum('nij,nj->ni',inv[ids],correction));np.add.at(count,ids,1)
    q+=.75*delta/np.maximum(count[:,None],1)
    for _ in range(20):
        axis=q[v]-q[u];length=np.linalg.norm(axis,axis=1);deficit=np.maximum(0,length0*.98-length);push=axis/np.maximum(length[:,None],1e-9)*deficit[:,None]*.5
        spring=np.zeros_like(q);np.add.at(spring,u,-push);np.add.at(spring,v,push);q+=spring/np.maximum(degree[:,None],1)
    if iteration%5==0:print('SURFACE_FIT',iteration,totals,maximum,flush=True);history.append({'iteration':iteration,'total':totals,'maximum':maximum})
    if sum(totals.values())==0:break
np.savez_compressed(ROOT/'build/skirt_clearance_fit.npz',P=q,W=w,source_P=original,object=name)
(ROOT/'reports/skirt_surface_fit.json').write_text(json.dumps({'history':history,'max_rest_displacement_m':float(np.linalg.norm(q-original,axis=1).max()),'game_verified':False},indent=2))
