"""Fit short depth capsules to the actual pelvis instead of tall round end caps."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from pelvis_support import surface_samples, clearance, pose_capsule

def fit_motion(caps,retained,source,root):
    import sys
    from workspace_paths import workspace_root
    sys.path.insert(0,str(workspace_root(root)/'tools/asset_helpers/previewer'))
    from baker.animation import parse_animjson,skin_matrices,lbs
    from baker.skeleton import parse_skeljson
    rig=parse_skeljson(json.loads((root/'reports/final_skeleton.json').read_text()))
    p=source['yqs_part_08_p'];w=source['yqs_part_08_w'];f=source['yqs_part_08_f']
    keep=(abs(p[:,0])<.2)&(p[:,2]>.82)&(p[:,2]<1.06);f=f[keep[f].all(1)]
    bi=np.argsort(-w,axis=1)[:,:4];bw=np.floor(np.take_along_axis(w,bi,axis=1)*255).astype(int);bw[:,0]+=255-bw.sum(1)
    original=np.array([c['radius_m'] for c in caps])
    for label in ['idle','run','bow','riding','slash']:
        anim=parse_animjson(json.loads((root/'reports'/(label+'.json')).read_text()))
        for frame in sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,12).astype(int))):
            skin=skin_matrices(rig,anim,frame);tri=lbs(p,bi,bw,skin)[f]
            points=np.concatenate([tri[:,0]*(i/4)+tri[:,1]*(j/4)+tri[:,2]*(1-(i+j)/4) for i in range(5) for j in range(5-i)])
            distances=[]
            for c in caps:
                a,b=pose_capsule(c,skin,rig['names']);axis=b-a;t=np.clip((points-a)@axis/(axis@axis),0,1)
                distances.append(np.linalg.norm(points-a-t[:,None]*axis,axis=1)-c['radius_m'])
            distances=np.array(distances);gap=distances.min(0);nearest=distances.argmin(0)
            others=[dict(c,endpoints_m=pose_capsule(c,skin,rig['names']).tolist()) for c in retained]
            uncovered=(gap>0)&(clearance(points,others)>0)
            for i in np.unique(nearest[uncovered]):
                caps[int(i)]['radius_m']+=float(gap[uncovered&(nearest==i)].max())+.0005
    added=np.array([c['radius_m'] for c in caps])-original
    assert added.max()<.03, ('Excessive local pose margin',float(added.max()))
    return dict(sampled_frames_per_pose=12,maximum_added_margin_m=float(added.max()),changed_capsules=int((added>0).sum()))

def fit(source, previous, root):
    points = np.unique(surface_samples(source['yqs_part_08_p'], source['yqs_part_08_f'], 6), axis=0)
    # The rigid waistband covers the upper abdomen; colliding with its inset roots creates an unsatisfiable constraint.
    points=points[points[:,2]<1.06]
    skirt = source['yqs_part_10_p']
    skirt = skirt[(skirt[:,2]>.82)&(skirt[:,2]<1.12)]
    retained = [dict(c) for c in previous if not c['name'].startswith('pelvis_')]
    for c in retained:
        if c['name']=='waist':c['radius_m']=.022
    transfer=json.loads((root/'reports/weight_transfer.json').read_text());names=transfer['native_bones']
    tree=cKDTree(source['yqs_part_08_p'])
    candidates=[]
    for columns,bands in [(3,4),(4,5),(5,6),(6,7)]:
        caps=[]
        xx=np.linspace(points[:,0].min(),points[:,0].max(),columns+1)
        zz=np.linspace(points[:,2].min(),points[:,2].max(),bands+1)
        for ix in range(columns):
            for iz in range(bands):
                q=points[(points[:,0]>=xx[ix])&(points[:,0]<=xx[ix+1])&(points[:,2]>=zz[iz])&(points[:,2]<=zz[iz+1])]
                if not len(q):continue
                cx=(q[:,0].min()+q[:,0].max())/2;cz=(q[:,2].min()+q[:,2].max())/2
                cy=(q[:,1].min()+q[:,1].max())/2;trim=min(np.ptp(q[:,1])*.15,.012)
                a=np.array([cx,min(q[:,1].min()+trim,cy-.0005),cz]);b=np.array([cx,max(q[:,1].max()-trim,cy+.0005),cz])
                axis=b-a;t=np.clip((q-a)@axis/(axis@axis),0,1)
                radius=float(np.linalg.norm(q-a-t[:,None]*axis,axis=1).max()+.002)
                weight=source['yqs_part_08_w'][tree.query(q)[1]].mean(0)
                owner=names[int(weight.argmax())]
                ids=np.argsort(-weight)[:2];values=weight[ids];values/=values.sum()
                influences=[dict(bone=names[int(i)],weight=float(v)) for i,v in zip(ids,values)]
                caps.append(dict(name=f'pelvis_{ix}_{iz}',endpoints_m=[a.tolist(),b.tolist()],radius_m=radius,bones=[owner,owner],endpoint_weights=[influences,influences]))
        combined=retained+caps
        gap=clearance(points,combined);pressure=np.maximum(-clearance(skirt,combined),0)
        assert gap.max()<=-.00199
        candidates.append((float(pressure.mean()),caps,dict(columns=columns,bands=bands,capsules=len(caps),body_minimum_clearance_m=float(-gap.max()),skirt_mean_overlap_m=float(pressure.mean()),skirt_max_overlap_m=float(pressure.max()))))
    _,caps,chosen=min(candidates,key=lambda x:x[0]+len(x[1])*.000002)
    motion=fit_motion(caps,retained,source,root)
    final_pressure=np.maximum(-clearance(skirt,retained+caps),0)
    before=np.maximum(-clearance(skirt,previous),0)
    assert final_pressure.mean()<before.mean()*.8
    report=dict(status='pass',method='Short depth-axis capsules fitted to full pelvis surface lattice; two-bone weights and local Native pose margins',baseline_mean_overlap_m=float(before.mean()),baseline_max_overlap_m=float(before.max()),final_mean_overlap_m=float(final_pressure.mean()),final_max_overlap_m=float(final_pressure.max()),motion=motion,selected=chosen,candidates=[x[2] for x in candidates],body_samples=len(points),skirt_vertices=len(skirt),game_verified=False)
    (root/'reports/pelvis_panel_fit.json').write_text(json.dumps(report,indent=2))
    print('PELVIS_PANEL_FIT',report,flush=True)
    return caps
