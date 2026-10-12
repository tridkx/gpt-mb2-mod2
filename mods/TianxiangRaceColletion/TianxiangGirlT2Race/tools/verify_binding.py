"""Check T2 bind directions and palm attachment points using final skeleton."""
import json,sys,numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R
cfg=json.loads((R/'tools/model_config.json').read_text());rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
S=np.array(cfg['landmarks_m']);assert np.max(abs(rig['restWorld'][:,:3,3]-S))<2e-6
angles=[]
for bone,start,end in [(15,15,17),(16,15,17),(17,17,19),(18,17,19),(22,22,24),(23,22,24),(24,24,26),(25,24,26)]:
    axis=rig['restWorld'][bone,:3,0];delta=S[end]-S[start];delta/=np.linalg.norm(delta)
    angle=float(np.degrees(np.arccos(np.clip(axis@delta,-1,1))))
    assert angle<.1,(bone,angle);angles.append({'bone':rig['names'][bone],'axis_deviation_degrees':angle})
a=np.load(R/'build/fitted_model.npz');part=cfg['hand_part'];p=a[part+'_p'];w=a[part+'_w'];tri=a[part+'_f']
assert (w[:,[20,27]]==0).all()
samples=[];weights=[]
for i in range(5):
    for j in range(5-i):
        bary=np.array([i,j,4-i-j])/4
        samples.append((p[tri]*bary[None,:,None]).sum(1));weights.append((w[tri]*bary[None,:,None]).sum(1))
p=np.concatenate(samples);w=np.concatenate(weights);inv=np.linalg.inv(rig['restWorld']);rows=[]
for label in ['rest','run','stand_onehand','stand_twohand','ui_neutral_male']:
    anim=None if label=='rest' else parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=[0] if anim is None else sorted(set(np.linspace(anim['start'],anim['frames']-1,24).astype(int)))
    maximum={'left':0,'right':0}
    for frame in frames:
        world=rig['restWorld'].copy()
        if anim is not None:
            for i,parent in enumerate(rig['parent']):
                local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame])
                if parent<0:local[:3,3]+=anim['rootPos'][frame]
                world[i]=local if parent<0 else world[parent]@local
        skin=world@inv;posed=np.zeros_like(p)
        for i in range(28):posed+=w[:,i,None]*(p@skin[i,:3,:3].T+skin[i,:3,3])
        for labelside,sign,item in [('left',-1,20),('right',1,27)]:
            q=posed[(p[:,0]*sign>.34)&(p[:,2]<.85)]
            maximum[labelside]=max(maximum[labelside],float(cKDTree(q).query(world[item,:3,3])[0]))
    assert max(maximum.values())<.025,(label,maximum)
    rows.append(dict(pose=label,frames=len(frames),maximum_attachment_to_sampled_hand_surface_m=maximum))
(R/'reports/binding_validation.json').write_text(json.dumps(dict(status='pass',version=cfg['version'],arm_axes=angles,grip_points=rows,source_joint_positions_preserved=True,item_bones_do_not_deform_hands=True,scope='Final bind directions and sampled hand surfaces; no engine weapon geometry, finger closure or IK test'),indent=2))
print('BINDING_PASS',rows)
