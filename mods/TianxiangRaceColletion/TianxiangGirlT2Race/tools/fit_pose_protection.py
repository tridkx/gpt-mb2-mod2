"""Fit additional local shorts caps to byte-skinned motion protection surfaces."""
import json,numpy as np
from scipy.spatial import cKDTree
from scipy.cluster.vq import kmeans2
from collision_helpers import R,cfg,rig,protection_mesh,native_skins,surface_samples,outside_union,endpoints

def fit_pose_protection(caps):
    mesh=protection_mesh(authored=True);tree=cKDTree(mesh['pos'])
    for cap in caps:
        if not cap['name'].startswith('shorts_patch_'):continue
        center=np.mean(cap['endpoints_m'],0);dist,ix=tree.query(center,k=16);w=np.zeros(28)
        for vi,d in zip(ix,dist):np.add.at(w,mesh['bi'][vi],mesh['bw'][vi]/max(d,.003))
        top=np.argsort(w)[-2:];ws={rig['names'][i]:float(w[i]/w[top].sum()) for i in top if w[i]>0}
        cap['endpoint_weights']=[ws,ws]
    poses=list(native_skins());rest=surface_samples(mesh,np.tile(np.eye(4),(28,1,1)));posed=[];miss=np.zeros(len(rest),bool)
    for _,_,skin in poses:
        q=surface_samples(mesh,skin);posed.append(q);miss|=outside_union(q,caps,skin)>-.002
    ids=np.flatnonzero(miss)
    if not len(ids):return caps
    _,groups=kmeans2(rest[ids],min(10,len(ids)),minit='++',seed=203)
    f=mesh['idx'].reshape(-1,3);bary=np.array([[i,j,6-i-j] for i in range(7) for j in range(7-i)])/6
    positions=np.einsum('bq,tqc->tbc',bary,mesh['pos'][f]).reshape(-1,3);lo,hi=cfg['shorts_height_band_m'];mask=(positions[:,2]>lo)&(positions[:,2]<hi)
    vw=np.zeros((len(mesh['pos']),28))
    for i in range(4):vw[np.arange(len(vw)),mesh['bi'][:,i]]+=mesh['bw'][:,i]/255
    weights=np.einsum('bq,tqk->tbk',bary,vw[f]).reshape(-1,28)[mask]
    for k in sorted(set(groups)):
        selected=ids[groups==k];center=rest[selected].mean(0);center[:2]*=.94;average=weights[selected].mean(0);top=np.argsort(average)[-2:];ws={rig['names'][i]:float(average[i]/average[top].sum()) for i in top if average[i]>0}
        cap=dict(name='pose_protection_'+str(k).zfill(2),endpoints_m=[(center+[-.002,0,0]).tolist(),(center+[.002,0,0]).tolist()],radius_m=0,bones=list(ws),endpoint_weights=[ws,ws],sample_count=len(selected),clearance_m=.003)
        required=0
        for q,(_,_,skin) in zip(posed,poses):
            a,b=endpoints(cap,skin);v=b-a;t=np.clip((q[selected]-a)@v/(v@v),0,1);required=max(required,float(np.linalg.norm(q[selected]-a-t[:,None]*v,axis=1).max()))
        cap['radius_m']=required+.003;caps.append(cap)
    return caps
