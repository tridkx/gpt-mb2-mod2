"""Fit additional local shorts caps to byte-skinned motion protection surfaces."""
import json,numpy as np
from scipy.cluster.vq import kmeans2
from collision_helpers import R,cfg,rig,protection_mesh,native_skins,surface_samples,outside_union,endpoints

def fit_pose_protection(caps):
    mesh=protection_mesh(authored=True)
    poses=list(native_skins());rest=surface_samples(mesh,np.tile(np.eye(4),(28,1,1)));posed=[];miss=np.zeros(len(rest),bool)
    for _,_,skin in poses:
        q=surface_samples(mesh,skin);posed.append(q);miss|=outside_union(q,caps,skin)>-.002
    ids=np.flatnonzero(miss)
    if not len(ids):return caps
    _,groups=kmeans2(rest[ids],min(cfg['shorts_local_capsules'],len(ids)),minit='++',seed=203)
    f=mesh['idx'].reshape(-1,3);bary=np.array([[i,j,6-i-j] for i in range(7) for j in range(7-i)])/6
    positions=np.einsum('bq,tqc->tbc',bary,mesh['pos'][f]).reshape(-1,3);lo,hi=cfg['shorts_height_band_m'];mask=(positions[:,2]>lo)&(positions[:,2]<hi)
    vw=np.zeros((len(mesh['pos']),28))
    for i in range(4):vw[np.arange(len(vw)),mesh['bi'][:,i]]+=mesh['bw'][:,i]/255
    weights=np.einsum('bq,tqk->tbk',bary,vw[f]).reshape(-1,28)[mask]
    # Score outward displacement against the actual upper active skirt in rest
    # and captured standing poses, rather than using coverage alone.
    from baker.animation import lbs
    cloth=next(json.loads(p.read_text()) for p in (R/'build/cloth_inputs').glob('*.mesh.json') if json.loads(p.read_text())['lod']==0)
    cp=np.array(cloth['positions']);mask=(cp[:,2]>.65)&(cp[:,2]<.86)&(np.array(cloth['alpha'])>0)
    static=[(skin,lbs(cp,np.array(cloth['bones']),np.array(cloth['weights']),skin)[mask]) for label,_,skin in poses if label in ['rest','captured_creation']]
    skins=np.array([skin for _,_,skin in poses])
    for k in sorted(set(groups)):
        selected=ids[groups==k];patch=rest[selected];center=patch.mean(0)
        average=weights[selected].mean(0);top=np.argsort(average)[-2:]
        ws={rig['names'][i]:float(average[i]/average[top].sum()) for i in top if average[i]>0}
        transform=sum(w*skins[:,rig['names'].index(n)] for n,w in ws.items())
        target=np.array([q[selected] for q in posed])
        _,_,axes=np.linalg.svd(patch-center,full_matrices=False);axis=axes[0]
        span=float(np.ptp((patch-center)@axis));radial=center.copy();radial[2]=0;radial/=max(np.linalg.norm(radial),1e-9)
        best=None
        for inward in [0,.006,.012,.025,.04]:
            for extent in [.001,.25,.5]:
                origin=center-radial*inward
                ep=np.array([origin-axis*span*extent,origin+axis*span*extent])
                world=np.einsum('pij,kj->pki',transform[:,:3,:3],ep)+transform[:,:3,3][:,None]
                a=world[:,0];v=world[:,1]-a
                t=np.clip(np.einsum('pni,pi->pn',target-a[:,None],v)/np.maximum(np.einsum('pi,pi->p',v,v)[:,None],1e-12),0,1)
                radius=float(np.linalg.norm(target-a[:,None]-t[:,:,None]*v[:,None],axis=2).max())+cfg['shorts_capsule_clearance_m']
                cap=dict(name='pose_protection_'+str(k).zfill(2),endpoints_m=ep.tolist(),radius_m=radius,bones=list(ws),endpoint_weights=[ws,ws],sample_count=len(selected),clearance_m=cfg['shorts_capsule_clearance_m'])
                pushes=[]
                for skin,skirt in static:
                    pushes.extend(np.maximum(-outside_union(skirt,[cap],skin),0))
                pushes=np.array(pushes);score=float(pushes.max()+pushes.mean()*2+radius*.02)
                if best is None or score<best[0]:best=(score,cap)
        best[1]['standing_skirt_push_score_m']=best[0];caps.append(best[1])
    return caps
