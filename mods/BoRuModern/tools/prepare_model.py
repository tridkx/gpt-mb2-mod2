"""Read preserved ActorX input, fit anatomy to native rest pose, split shared cuts."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.interpolate import RBFInterpolator
ROOT=Path(__file__).resolve().parents[1]; WORKSPACE=ROOT.parents[1]
LEG_WIDTH_SCALE=.64  # v1.0.0 .80, further 20% narrower per user feedback.
LEG_DEPTH_SCALE=.85
SHOE_WIDTH_SCALE=.6375  # v1.0.0 .85, further 25% narrower.
SHOE_EXTRA_WIDTH_SCALE=.90  # v1.0.3: another 10%, taper to unchanged sock rim.
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
import psk_lib

p=psk_lib.check(psk_lib.read(ROOT/'input/SK_BR_nofoot.psk'))
b=p['bones']; bn={x['name'].decode():i for i,x in enumerate(b)}
world=[]
for i,x in enumerate(b):
    q=x['quat'].astype(float).copy()
    if i:q[:3]*=-1 # ActorX stores conjugate local rotations below root.
    m=np.eye(4);m[:3,:3]=Rotation.from_quat(q).as_matrix();m[:3,3]=x['pos']
    world.append(m if i==0 else world[int(x['parent'])]@m)
C=np.diag([-1.,-1.,1.]); points=p['points']@C.T*.01
anatomy={name:world[i][:3,3]@C.T*.01 for name,i in bn.items()}
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
names=rig['names'];ni={n:i for i,n in enumerate(names)};target=rig['restWorld'][:,:3,3];source=target.copy()
landmarks={'pelvis':'pelvis','spine':'spine_01','spine1':'spine_03','neck':'neck_01','head':'head'}
for side in ['l','r']:
    for dst,src in [('clavicle','clavicle'),('upperarm_twist','upperarm'),('foretwist','lowerarm'),('hand','hand'),('finger0','middle_01'),('thigh','thigh'),('calf','calf'),('foot','foot'),('toe0','ball')]:
        landmarks[side+'_'+dst]=src+'_'+side
for dst,src in landmarks.items():source[ni[dst]]=anatomy[src]
source[ni['spine2']]=(anatomy['spine_03']+anatomy['neck_01'])/2
for side in ['l','r']:
    for mid,a,end in [('upperarm_twist1','upperarm_twist','foretwist'),('foretwist1','foretwist','hand')]:source[ni[side+'_'+mid]]=(source[ni[side+'_'+a]]+source[ni[side+'_'+end]])/2
nextname={'pelvis':'spine','spine':'spine1','spine1':'spine2','spine2':'neck','neck':'head'}
for side in ['l','r']:
    for a,end in [('clavicle','upperarm_twist'),('upperarm_twist','foretwist'),('upperarm_twist1','foretwist'),('foretwist','hand'),('foretwist1','hand'),('hand','finger0'),('thigh','calf'),('calf','foot'),('foot','toe0')]:nextname[side+'_'+a]=side+'_'+end
transforms=[]
for i,name in enumerate(names):
    if name not in nextname:transforms.append(np.eye(3));continue
    j=ni[nextname[name]];a=source[j]-source[i];d=target[j]-target[i];aa=a/np.linalg.norm(a);dd=d/np.linalg.norm(d)
    v=np.cross(aa,dd);k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    rot=np.eye(3)+k+k@k/max(1+aa@dd,1e-8)
    transforms.append(rot@(np.eye(3)+(np.linalg.norm(d)/np.linalg.norm(a)-1)*np.outer(aa,aa)))
transforms=np.array(transforms)
anchors=[i for i,n in enumerate(names) if not any(x in n for x in ['twist1','finger0','toe0'])]
warp=RBFInterpolator(source[anchors][:,[0,2]],target[anchors]-source[anchors],kernel='thin_plate_spline',smoothing=1e-7)
def smooth(a,end,x):
    t=np.clip((x-a)/(end-a),0,1);return t*t*(3-2*t)
def deform_base(q):
    out=q+warp(q[:,[0,2]])
    for side in ['l','r']:
        ids=[ni[side+'_'+s] for s in ['upperarm_twist','foretwist','hand']];ds=[]
        for i in ids:
            axis=source[ni[nextname[names[i]]]]-source[i];t=np.clip((q-source[i])@axis/(axis@axis),0,1)
            ds.append(np.linalg.norm(q-source[i]-t[:,None]*axis,axis=1))
        ds=np.stack(ds,1);ww=np.exp(np.maximum(-(ds-ds.min(1,keepdims=True))/.02,-40));ww/=ww.sum(1,keepdims=True)
        fit=sum(ww[:,j,None]*((q-source[i])@transforms[i].T+target[i]) for j,i in enumerate(ids))
        amount=smooth(.11,.23,np.abs(q[:,0]))*smooth(1.1,1.24,q[:,2])*(q[:,0]<0 if side=='l' else q[:,0]>0)
        out=out*(1-amount[:,None])+fit*amount[:,None]
        # Preserve complete hand shape after the wrist, without finger stretching.
        i=ni[side+'_hand'];u,_,vt=np.linalg.svd(transforms[i]);rot=u@vt
        rigid=(q-source[i])@rot.T+target[i];amount=smooth(.52,.585,np.abs(q[:,0]))*(q[:,0]<0 if side=='l' else q[:,0]>0)*smooth(1.15,1.25,q[:,2])
        out=out*(1-amount[:,None])+rigid*amount[:,None]
    amount=smooth(1.385,1.47,q[:,2])*(1-smooth(.105,.20,np.abs(q[:,0])))
    rigid=q+target[ni['head']]-source[ni['head']]
    out=out*(1-amount[:,None])+rigid*amount[:,None]
    # User requested a larger head; one field scales face/hair/glasses together
    # and tapers into the shared neck rather than opening the equipment cut.
    amount=smooth(1.41,1.49,q[:,2])*(1-smooth(.12,.20,np.abs(q[:,0])))
    pivot=np.array([0.,anatomy['head'][1],1.535])+target[ni['head']]-source[ni['head']]
    out=pivot+(out-pivot)*(1+.12*amount[:,None])
    return out

def narrow_feet(q,out):
    for side in ['l','r']:
        anchor=target[ni[side+'_foot']];axis=target[ni[side+'_toe0']][:2]-anchor[:2];axis/=np.linalg.norm(axis)
        lateral=np.array([-axis[1],axis[0]])
        amount=(1-smooth(.14,.23,q[:,2]))*(q[:,0]<0 if side=='l' else q[:,0]>=0)
        transverse=(out[:,:2]-anchor[:2])@lateral
        out[:,:2]-=(1-SHOE_WIDTH_SCALE)*amount[:,None]*transverse[:,None]*lateral
    return out

def deform_shoes(q):
    out=narrow_feet(q,deform_base(q))
    for side in ['l','r']:
        anchor=target[ni[side+'_foot']];axis=target[ni[side+'_toe0']][:2]-anchor[:2];axis/=np.linalg.norm(axis)
        lateral=np.array([-axis[1],axis[0]])
        amount=(1-smooth(.105,.135,q[:,2]))*(q[:,0]<0 if side=='l' else q[:,0]>=0)
        transverse=(out[:,:2]-anchor[:2])@lateral
        out[:,:2]-=(1-SHOE_EXTRA_WIDTH_SCALE)*amount[:,None]*transverse[:,None]*lateral
    return out

def deform(q):
    out=deform_base(q)
    amount=smooth(.145,.215,q[:,2])*(1-smooth(.90,1.00,q[:,2]))
    for side in ['l','r']:
        select=q[:,0]<0 if side=='l' else q[:,0]>=0
        # Contract cross sections around their fitted anatomical center line,
        # retaining native joint positions and longitudinal coordinates.
        joints=np.array([anatomy['foot_'+side],anatomy['calf_'+side],anatomy['thigh_'+side]])
        centers=q.copy()
        centers[:,0]=np.interp(q[:,2],joints[:,2],joints[:,0])
        centers[:,1]=np.interp(q[:,2],joints[:,2],joints[:,1])
        fitted_centers=deform_base(centers)
        a=amount*select
        out[:,0]=fitted_centers[:,0]+(out[:,0]-fitted_centers[:,0])*(1-(1-LEG_WIDTH_SCALE)*a)
        out[:,1]=fitted_centers[:,1]+(out[:,1]-fitted_centers[:,1])*(1-(1-LEG_DEPTH_SCALE)*a)
    return narrow_feet(q,out)

def deform_skin(q):
    out=deform(q)
    amount=smooth(.18,.235,q[:,2])*(1-smooth(.25,.27,q[:,2]))
    for side in ['l','r']:
        joints=np.array([anatomy['foot_'+side],anatomy['calf_'+side],anatomy['thigh_'+side]])
        centers=q.copy()
        for axis in [0,1]:centers[:,axis]=np.interp(q[:,2],joints[:,2],joints[:,axis])
        center=deform(centers);selected=q[:,0]<0 if side=='l' else q[:,0]>=0
        a=amount*selected
        out[:,:2]=center[:,:2]+(out[:,:2]-center[:,:2])*(1-.18*a[:,None])
    return out

# Map original UE/CC body skin; merge face and separate digit influences.
mapping={'root':'pelvis','pelvis':'pelvis','spine_01':'spine','spine_02':'spine1','spine_03':'spine2','neck_01':'neck','head':'head','cc_base_l_ribstwist':'spine2','cc_base_r_ribstwist':'spine2'}
for side in ['l','r']:
    for src,dst in [('clavicle','clavicle'),('upperarm','upperarm_twist'),('upperarm_twist_01','upperarm_twist1'),('lowerarm','foretwist'),('lowerarm_twist_01','foretwist1'),('hand','hand'),('thigh','thigh'),('thigh_twist_01','thigh'),('calf','calf'),('calf_twist_01','calf'),('foot','foot'),('ball','toe0')]:mapping[src+'_'+side]=side+'_'+dst
mapped=[]
for x in b:
    n=x['name'].decode()
    if n.startswith('cc_base_') and n not in mapping:n='head'
    if any(n.startswith(x+'_') for x in ['index','middle','ring','pinky','thumb']):n='hand_'+n[-1]
    mapped.append(ni[mapping.get(n,'pelvis')])
weights=np.zeros((len(points),len(names)))
wt=p['weights'];np.add.at(weights,(wt['pt'],np.array(mapped)[wt['bone']]),wt['weight'])
# All neck skin uses one field, independent of equipment boundaries.
h=smooth(1.385,1.47,points[:,2]);amount=smooth(1.365,1.385,points[:,2])*(1-smooth(.105,.20,np.abs(points[:,0])))
weights*=1-amount[:,None];weights[:,ni['neck']]+=amount*(1-h);weights[:,ni['head']]+=amount*h
# A fixed hand follows the native palm; wrist skin blends smoothly.
for side in ['l','r']:
    amount=smooth(.52,.585,np.abs(points[:,0]))*(points[:,0]<0 if side=='l' else points[:,0]>0)*smooth(1.15,1.25,points[:,2])
    weights*=1-amount[:,None];weights[:,ni[side+'_hand']]+=amount
weights/=weights.sum(1,keepdims=True)

# Original crotch skin jumps between left/right legs over a few millimeters.
# Native leg spread magnifies that discontinuity; blend pelvis and both thighs
# with one continuous source-space field shared by jeans and underlying skin.
amount=(1-smooth(.08,.20,np.abs(points[:,0])))*smooth(.70,.78,points[:,2])*(1-smooth(.97,1.01,points[:,2]))
leg=1-smooth(.78,.95,points[:,2]);right=smooth(-.04,.04,points[:,0]);lower=np.zeros_like(weights)
lower[:,ni['pelvis']]=1-leg;lower[:,ni['l_thigh']]=leg*(1-right);lower[:,ni['r_thigh']]=leg*right
weights=weights*(1-amount[:,None])+lower*amount[:,None]
# One continuous ankle field is shared by the exposed skin and sock opening.
# The sole stays rigid; the sock rim increasingly follows the calf.
low=points[:,2]<.26
for side in ['l','r']:
    selected=low & (points[:,0]<0 if side=='l' else points[:,0]>=0)
    calf=smooth(.105,.24,points[selected,2]);blend=1-smooth(.24,.26,points[selected,2])
    local=np.zeros_like(weights[selected]);local[:,ni[side+'_calf']]=calf;local[:,ni[side+'_foot']]=1-calf
    weights[selected]=weights[selected]*(1-blend[:,None])+local*blend[:,None]

wed=p['wedges'];faces=p['faces'];tri=wed['pt'][np.stack([faces['w0'],faces['w1'],faces['w2']],1)]
norm=np.zeros_like(points);fn=np.cross(points[tri[:,1]]-points[tri[:,0]],points[tri[:,2]]-points[tri[:,0]])
for j in range(3):np.add.at(norm,tri[:,j],fn)
norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)

# Cut triangles geometrically, interpolate all attributes, keep matching cuts.
def clip(poly,axis,cut,above):
    out=[]
    for a,d in zip(poly,poly[1:]+poly[:1]):
        va=a[axis]-cut;vd=d[axis]-cut;ia=va>=-1e-10 if above else va<=1e-10;ib=vd>=-1e-10 if above else vd<=1e-10
        if ia:out.append(a)
        if ia!=ib:
            t=va/(va-vd);v=a+t*(d-a);v[axis]=cut;out.append(v)
    return out
parts={};original_areas=0;split_areas=0
for fi,face in enumerate(faces):
    wi=np.array([face['w0'],face['w1'],face['w2']]);ids=wed['pt'][wi];slot=int(face['mat'])
    uv=np.stack([wed['u'][wi],1-wed['v'][wi]],1)
    poly=[v for v in np.concatenate([points[ids],norm[ids],uv,weights[ids]],1)]
    polygons=[poly]
    if slot==0:
        for axis,cut in [(2,1.42),(0,-.555),(0,.555),(2,.145),(2,.25),(0,-.385),(0,.385),(2,1.25)]:
            new=[]
            for pg in polygons:
                if min(v[axis] for v in pg)<cut<max(v[axis] for v in pg):new.extend([clip(pg,axis,cut,True),clip(pg,axis,cut,False)])
                else:new.append(pg)
            polygons=[pg for pg in new if len(pg)>=3]
    for pg in polygons:
        center=np.mean([v[:3] for v in pg],0)
        if slot==6:part='head';mat='hair'
        elif slot in [1,2,3]:part='head';mat={1:'mouth',2:'sclera',3:'eyes'}[slot]
        elif slot==4:part='head' if center[2]>1.45 else 'hands';mat='glass' if part=='head' else 'accessory'
        elif slot==5:part='legs' if center[2]<.145 else ('hands' if abs(center[0])>.54 else 'body');mat='cloth'
        else:
            part='head' if center[2]>1.42 else ('hands' if abs(center[0])>.555 else ('legs' if center[2]<.145 else 'body'));mat='skin'
            # Eye fringe cards have a dedicated region in the body opacity atlas.
            if all(.299<v[6]<.408 and .40<1-v[7]<.53 for v in pg) and 1.52<center[2]<1.545:mat='lashes'
            # Preserve exposed neck, arms and ankles; omit skin hidden beneath
            # shirt and jeans so large poses cannot reveal the interior body.
            if mat=='skin' and part=='body' and not (center[2]<.25 or (abs(center[0])>.385 and center[2]>1.2) or (center[2]>1.25 and abs(center[0])<.145)):continue
        name='boru_'+part+'_'+mat
        store=parts.setdefault(name,{'part':part,'material':mat,'rows':[],'f':[],'dedup':{}})
        for j in range(1,len(pg)-1):
            rows=[pg[0],pg[j],pg[j+1]]
            if np.linalg.norm(np.cross(rows[1][:3]-rows[0][:3],rows[2][:3]-rows[0][:3]))<1e-12:continue
            idx=[]
            for v in rows:
                key=tuple(np.round(v,7))
                if key not in store['dedup']:store['dedup'][key]=len(store['rows']);store['rows'].append(v)
                idx.append(store['dedup'][key])
            store['f'].append(idx)
data={};manifest=[]
for name,rec in parts.items():
    arr=np.array(rec['rows']);q=arr[:,:3].copy();w=arr[:,8:].copy()
    if rec['part']=='legs' and rec['material']=='skin':
        # Preserve the shared equipment cut at .145m, but extend the original
        # open .135m cut 4.5cm into the sock. The hidden tail follows the foot.
        extension=1-smooth(.135,.145,q[:,2]);q[:,2]-=.045*extension
        for side in ['l','r']:
            select=(extension>1e-7)&(q[:,0]<0 if side=='l' else q[:,0]>=0)
            calf=smooth(.105,.24,q[select,2]);w[select]=0
            w[select,ni[side+'_calf']]=calf;w[select,ni[side+'_foot']]=1-calf
    fit_fn=deform_shoes if rec['part']=='legs' else (deform_skin if rec['part']=='body' and rec['material']=='skin' else deform);fitted=fit_fn(q)
    if rec['material']=='eyes':
        # The supplied eye map is a planar iris disc, not a globe UV atlas.
        # Project around the measured front corneal centers instead of wrapping
        # the old globe UVs, which would magnify the pupil over the whole eye.
        centers_x=np.where(q[:,0]<0,-.02897,.02897)
        arr[:,6]=.5+(q[:,0]-centers_x)/.03
        arr[:,7]=.5+(q[:,2]-1.53284)/.03
    if rec['material'] in ['hair','mouth','eyes','sclera','lashes','glass']:w[:]=0;w[:,ni['head']]=1
    normal=arr[:,3:6];jac=np.stack([(fit_fn(q+np.eye(3)[i]*1e-5)-fitted)/1e-5 for i in range(3)],2)
    n=np.linalg.solve(jac.transpose(0,2,1),normal[:,:,None])[:,:,0];n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
    keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True)
    for key,a in [('p',fitted),('n',n),('uv',arr[:,6:8]),('w',w),('f',np.array(rec['f']))]:data[name+'_'+key]=a.astype('i4' if key=='f' else 'f4')
    manifest.append({'object':name,'part':rec['part'],'material':rec['material'],'vertices':len(q),'triangles':len(rec['f']),'kind':'hair' if rec['material']=='hair' else ('face' if rec['part']=='head' else 'cloth')})
# Exactly matched positions across cut pieces share normals and quantized skin.
bucket={}
for rec in manifest:
    if rec['material']!='skin':continue
    name=rec['object']
    for i,q in enumerate(data[name+'_p']):bucket.setdefault(tuple(np.round(q,6)),[]).append((name,i))
shared=0
for refs in bucket.values():
    if len({n for n,i in refs})<2:continue
    shared+=1
    for key in ['p','n','w']:
        a=np.mean([data[n+'_'+key][i] for n,i in refs],0)
        if key=='n':a/=max(np.linalg.norm(a),1e-12)
        for n,i in refs:data[n+'_'+key][i]=a
np.savez_compressed(ROOT/'build/fitted_model.npz',**data)
(ROOT/'build/manifest.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'reports/weight_transfer.json').write_text(json.dumps({'native_bones':names,'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'source_to_native_mapping':{x['name'].decode():names[mapped[i]] for i,x in enumerate(b)},'source_bounds':points.min(0).tolist()+points.max(0).tolist(),'shared_cut_points':shared,'facial_animation':False,'fixed_hands':True,'method':'Original ActorX weights mapped to native rig; common spatial fitting field; exact triangle cuts with interpolated skin.'},indent=2))
print('MODEL_PREPARED',manifest)
