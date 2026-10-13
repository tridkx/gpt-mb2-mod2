"""Preserve ActorX geometry; map source skin to a source-sized native semantic rig."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import psk_lib
R=Path(__file__).resolve().parents[1];W=R.parents[1]
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
cfg=json.loads((R/'tools/model_config.json').read_text());C=np.array(cfg['source_rotation']);scale=cfg['source_scale']
p=psk_lib.check(psk_lib.read(R/'input/SK_BR_nofoot.psk'));b=p['bones'];bn={x['name'].decode():i for i,x in enumerate(b)}
world=[]
for i,x in enumerate(b):
    q=x['quat'].astype(float).copy()
    if i:q[:3]*=-1
    m=np.eye(4);m[:3,:3]=Rotation.from_quat(q).as_matrix();m[:3,3]=x['pos']
    world.append(m if i==0 else world[int(x['parent'])]@m)
anatomy={n:world[i][:3,3]@C.T*scale for n,i in bn.items()}
raw=json.loads((R/'reports/human_skeleton.json').read_text());rig=parse_skeljson(raw);names=rig['names'];ni={n:i for i,n in enumerate(names)};S=rig['restWorld'][:,:3,3].copy()
mapping={'root':'pelvis','pelvis':'pelvis','spine_01':'spine','spine_02':'spine1','spine_03':'spine2','neck_01':'neck','head':'head','cc_base_l_ribstwist':'spine2','cc_base_r_ribstwist':'spine2'}
for side in ['l','r']:
    for src,dst in [('clavicle','clavicle'),('upperarm','upperarm_twist'),('upperarm_twist_01','upperarm_twist1'),('lowerarm','foretwist'),('lowerarm_twist_01','foretwist1'),('hand','hand'),('thigh','thigh'),('thigh_twist_01','thigh'),('calf','calf'),('calf_twist_01','calf'),('foot','foot'),('ball','toe0')]:mapping[src+'_'+side]=side+'_'+dst
landmarks={'pelvis':'pelvis','spine':'spine_01','spine1':'spine_02','spine2':'spine_03','neck':'neck_01','head':'head'}
for side in ['l','r']:
    for dst,src in [('clavicle','clavicle'),('upperarm_twist','upperarm'),('foretwist','lowerarm'),('hand','hand'),('finger0','middle_01'),('thigh','thigh'),('calf','calf'),('foot','foot'),('toe0','ball')]:landmarks[side+'_'+dst]=src+'_'+side
for dst,src in landmarks.items():S[ni[dst]]=anatomy[src]
for side in ['l','r']:
    for mid,a,end in [('upperarm_twist1','upperarm_twist','foretwist'),('foretwist1','foretwist','hand')]:S[ni[side+'_'+mid]]=(S[ni[side+'_'+a]]+S[ni[side+'_'+end]])/2
# Align each arm chain's binding direction to the source pose, preserving native roll.
custom=rig['restWorld'].copy();custom[:,:3,3]=S;directions={}
for side in ['l','r']:
    for a,end in [('clavicle','upperarm_twist'),('upperarm_twist','foretwist'),('upperarm_twist1','foretwist'),('foretwist','hand'),('foretwist1','hand'),('hand','finger0')]:directions[side+'_'+a]=side+'_'+end
for name,end in directions.items():
    i,j=ni[name],ni[end];a=rig['restWorld'][j,:3,3]-rig['restWorld'][i,:3,3];d=S[j]-S[i];a/=np.linalg.norm(a);d/=np.linalg.norm(d)
    v=np.cross(a,d);k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    rot=np.eye(3)+k+k@k/max(1+a@d,1e-8);custom[i,:3,:3]=rot@custom[i,:3,:3]
local=np.array([custom[i] if par<0 else np.linalg.inv(custom[par])@custom[i] for i,par in enumerate(rig['parent'])])
(R/'build/skeleton_spec.json').write_text(json.dumps([dict(name=n,parent=int(rig['parent'][i]),rest=local[i].T.reshape(-1).tolist()) for i,n in enumerate(names)],indent=2))
points=p['points']@C.T*scale;weights=np.zeros((len(points),len(names)));mapped=[]
for x in b:
    n=x['name'].decode()
    if n.startswith('cc_base_') and n not in mapping:n='head'
    if any(n.startswith(t+'_') for t in ['index','middle','ring','pinky','thumb']):n='hand_'+n[-1]
    if n.startswith('ik_'):
        assert not np.any(p['weights']['bone']==len(mapped)), 'IK helper unexpectedly weighted'
        n='pelvis'
    assert n in mapping,n
    mapped.append(ni[mapping[n]])
wt=p['weights'];np.add.at(weights,(wt['pt'],np.array(mapped)[wt['bone']]),wt['weight'])
weights/=weights.sum(1,keepdims=True)
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
# Source crotch weights switch legs over millimeters. Use a continuous field
# for skin and jeans so native alternating leg motion cannot tear the midline.
amount=(1-smooth(.08,.20,np.abs(points[:,0])))*smooth(.70,.78,points[:,2])*(1-smooth(.97,1.01,points[:,2]))
leg=1-smooth(.78,.95,points[:,2]);right=smooth(-.04,.04,points[:,0]);lower=np.zeros_like(weights)
lower[:,ni['pelvis']]=1-leg;lower[:,ni['l_thigh']]=leg*(1-right);lower[:,ni['r_thigh']]=leg*right
weights=weights*(1-amount[:,None])+lower*amount[:,None]
# Shoes remain rigid near the sole; sock and exposed ankle share a smooth cuff.
for side in ['l','r']:
    selected=(points[:,2]<.26)&(points[:,0]<0 if side=='l' else points[:,0]>=0)
    calf=smooth(.105,.24,points[selected,2]);blend=1-smooth(.24,.26,points[selected,2]);localw=np.zeros_like(weights[selected])
    localw[:,ni[side+'_calf']]=calf;localw[:,ni[side+'_foot']]=1-calf
    weights[selected]=weights[selected]*(1-blend[:,None])+localw*blend[:,None]
wed=p['wedges'];faces=p['faces'];tris=wed['pt'][np.stack([faces['w0'],faces['w1'],faces['w2']],1)]
norm=np.zeros_like(points);fn=np.cross(points[tris[:,1]]-points[tris[:,0]],points[tris[:,2]]-points[tris[:,0]])
for j in range(3):np.add.at(norm,tris[:,j],fn)
norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
parts={}
for fi,face in enumerate(faces):
    wi=np.array([face['w0'],face['w1'],face['w2']]);ids=wed['pt'][wi];slot=int(face['mat']);q=points[ids];center=q.mean(0);uv=np.stack([wed['u'][wi],1-wed['v'][wi]],1)
    mat={0:'skin',1:'mouth',2:'sclera',3:'eyes',4:'glass' if center[2]>1.45 else 'accessory',5:'cloth',6:'hair'}[slot]
    if slot==0 and all(.299<x<.408 for x in uv[:,0]) and all(.40<x<.53 for x in 1-uv[:,1]) and 1.52<center[2]<1.545:mat='lashes'
    w=weights[ids].copy()
    if mat in ['hair','mouth','eyes','sclera','lashes','glass']:w[:]=0;w[:,ni['head']]=1
    # Iris input is a planar disc; retain geometry but explicitly repair only eye UV.
    if mat=='eyes':uv[:,0]=.5+(q[:,0]-np.where(q[:,0]<0,-.02897,.02897))/.03;uv[:,1]=.5+(q[:,2]-1.53284)/.03
    rows=np.concatenate([q,norm[ids],uv,w],1);rec=parts.setdefault(mat,dict(rows=[],f=[],ids=[],dedup={}))
    idx=[]
    for v,pid in zip(rows,ids):
        key=tuple(np.round(v,7))
        if key not in rec['dedup']:rec['dedup'][key]=len(rec['rows']);rec['rows'].append(v);rec['ids'].append(int(pid))
        idx.append(rec['dedup'][key])
    rec['f'].append(idx)
data={};manifest=[]
for mat,rec in parts.items():
    arr=np.array(rec['rows']);w=arr[:,8:];keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True);name='boru_race_'+mat+'_mesh'
    for key,a in [('p',arr[:,:3]),('n',arr[:,3:6]),('uv',arr[:,6:8]),('w',w),('f',np.array(rec['f'])),('source_ids',np.array(rec['ids']))]:data[name+'_'+key]=a.astype('i4' if key in ['f','source_ids'] else 'f4')
    manifest.append(dict(object=name,part='body',material=mat,kind='hair' if mat in ['hair','lashes'] else 'body',vertices=len(arr),triangles=len(rec['f'])))
assert sum(r['triangles'] for r in manifest)==len(faces)
np.savez_compressed(R/'build/fitted_model.npz',**data);(R/'build/manifest.json').write_text(json.dumps(manifest,indent=2))
cfg['landmarks_m']=S.tolist();(R/'tools/model_config.json').write_text(json.dumps(cfg,indent=2))
hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'input').rglob('*') if p.is_file()};(R/'reports/input_hashes.json').write_text(json.dumps(hashes,indent=2))
(R/'reports/weight_transfer.json').write_text(json.dumps(dict(source_proportions_preserved=True,anatomy_warp=False,height_m=float(np.ptp(points[:,2])),uniform_scale=scale,rotation=C.tolist(),source_bones=80,target_bones=28,source_triangles=len(faces),mapping={x['name'].decode():names[mapped[i]] for i,x in enumerate(b)},landmarks_m=S.tolist(),arm_binding_direction_aligned=True,fixed_hands=True),indent=2))
print('MODEL_READY',manifest)
