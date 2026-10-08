"""Approximate PBD gravity/capsule screening, explicitly not Bannerlord physics."""
from pathlib import Path
import json
import numpy as np
from sleeve_motion import skin_frames,posed
ROOT=Path(__file__).resolve().parents[1]
meshes={m['name']:m for m in json.loads((ROOT/'build/sleeve_final.json').read_text())}
old={m['name']:m for m in json.loads((ROOT/'build/sleeve_baseline/meshes.json').read_text())}
mask=np.load(ROOT/'build/sleeve_mask.npz')
ids=np.where(mask['streamers'])[0]
mapping=np.full(len(mask['pos']),-1);mapping[ids]=np.arange(len(ids))
e=mask['edges'];e=e[np.all(mapping[e]>=0,axis=1)];e=mapping[e]
rest=np.linalg.norm(mask['pos'][ids][e[:,0]]-mask['pos'][ids][e[:,1]],axis=1)
# Disjoint edge batches permit stable Gauss-Seidel constraints without ordering
# dependence on array scatter behavior.
batches=[]
for edge in e:
    for batch in batches:
        if not any(v in batch[1] for v in edge):batch[0].append(edge);batch[1].update(edge);break
    else:batches.append(([edge],set(edge)))
batches=[np.array(b[0]) for b in batches]
edge_rest={tuple(edge):length for edge,length in zip(e,rest)}
batch_rest=[np.array([edge_rest[tuple(edge)] for edge in batch]) for batch in batches]
rig=json.loads((ROOT/'reports/human_skeleton.json').read_text())

def settle(anchor,distance,world):
    fixed=distance==0;inv_mass=(~fixed).astype(float)
    x=anchor.copy();previous=x.copy();dt=1/120
    capsules=[(15,17,.065),(17,19,.052),(22,24,.065),(24,26,.052),(0,11,.13)]
    for step in range(300):
        before=x.copy();x+=(x-previous)*.985+np.array([0,0,-9.81])*dt*dt*inv_mass[:,None];previous=before
        for iteration in range(48):
            for batch,length in zip(batches,batch_rest):
                a,b=batch.T;d=x[b]-x[a];norm=np.maximum(np.linalg.norm(d,axis=1),1e-9)
                denominator=np.maximum(inv_mass[a]+inv_mass[b],1)
                correction=d*((norm-length)/norm/denominator)[:,None]
                x[a]+=correction*inv_mass[a,None];x[b]-=correction*inv_mass[b,None]
            for a,b,radius in capsules:
                start=world[a,:3,3];axis=world[b,:3,3]-start
                t=np.clip((x-start)@axis/max(axis@axis,1e-9),0,1)
                center=start+t[:,None]*axis;d=x-center;norm=np.maximum(np.linalg.norm(d,axis=1),1e-9)
                # Near-root geometry already rests against the character skin;
                # proxy capsules cannot resolve that fitted seam accurately.
                contact=(norm<radius)&(~fixed)&(distance>.08)
                x[contact]=center[contact]+d[contact]/norm[contact,None]*radius
            delta=x-anchor;norm=np.maximum(np.linalg.norm(delta,axis=1),1e-9)
            x=anchor+delta*np.minimum(1,distance/norm)[:,None];x[fixed]=anchor[fixed]
    assert np.isfinite(x).all()
    strain=np.abs(np.linalg.norm(x[e[:,0]]-x[e[:,1]],axis=1)/rest-1)
    return x,{'max_displacement_m':float(np.linalg.norm(x-anchor,axis=1).max()),'mean_displacement_m':float(np.linalg.norm(x-anchor,axis=1).mean()),'edge_strain_p95':float(np.percentile(strain,95)),'fixed_point_error_m':float(np.linalg.norm(x[fixed]-anchor[fixed],axis=1).max())}

summary=[]
for label,filename in [('idle','idle'),('block','grip_twohanded_block'),('bow','bow')]:
    anim=json.loads((ROOT/f'reports/{filename}.json').read_text())
    skins,worlds=skin_frames(rig,anim)
    frame=0 if label=='idle' else int(np.argmax(worlds[:,[19,26],2,3].mean(1)))
    for variant,source in [('before',old),('after',meshes)]:
        arrays={name:posed(meshes[name],skins[frame]) for name in meshes if meshes[name]['lod']==0}
        anchor=arrays['tx5_body_00'][ids]
        travel=np.array(source['tx5_body_00']['color'])[ids,3]/255*source['tx5_body_00']['multiplier']
        result,metrics=settle(anchor,travel,worlds[frame]);arrays['tx5_body_00'][ids]=result
        np.savez_compressed(ROOT/f'build/sleeve_preview_{variant}_{label}.npz',**arrays)
        summary.append({'pose':label,'variant':variant,'native_frame':frame+1,**metrics})
report={'method':'Approximate position-based gravity and arm/torso capsule screening, static native poses. Not Bannerlord solver; no self/horse collision or fabric parameter equivalence.','results':summary}
(ROOT/'reports/sleeve_proxy_preview.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
