"""Preserve cha200 appearance and transfer cha800 skin to the native rig."""
import json,sys,shutil,hashlib,subprocess
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import RBFInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parents[2]
sys.path.insert(0,'D:/dsh-mod/re4-remake/tools')
from scan_mesh import load_mesh
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson

def obj(path):
    p=[];uv=[];n=[];groups={};mat=''
    for line in path.open(encoding='utf8'):
        s=line.split()
        if not s:continue
        if s[0]=='v':p.append(list(map(float,s[1:4])))
        elif s[0]=='vt':uv.append(list(map(float,s[1:3])))
        elif s[0]=='vn':n.append(list(map(float,s[1:4])))
        elif s[0]=='usemtl':mat=s[1];groups.setdefault(mat,[])
        elif s[0]=='f':
            corners=[tuple(int(x)-1 for x in token.split('/')) for token in s[1:]]
            for j in range(1,len(corners)-1):groups[mat].append([corners[0],corners[j],corners[j+1]])
    return np.array(p),np.array(uv),np.array(n),groups

# This proper rotation changes RE Y-up/+Z forward/+X left to native Z-up/+Y forward.
C=np.array([[-1,0,0],[0,0,1],[0,1,0]],float)
native=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
target=native['restWorld'][:,:3,3]
names=native['names'];ni={n:i for i,n in enumerate(names)}
source_json=json.loads((ROOT/'input/cha200/cha200_00_skeleton.json').read_text())
anatomy={b['name']:np.array(b['worldMatrix'])[3,:3]@C.T for b in source_json['bones']}
source=target.copy()
mapping={'Hip':'pelvis','Spine_0':'spine','Spine_1':'spine1','Spine_2':'spine2','Neck_0':'neck','Neck_1':'neck','Head':'head'}
landmarks={'pelvis':'Hip','spine':'Spine_0','spine1':'Spine_1','spine2':'Spine_2','neck':'Neck_0','head':'Head'}
for side,pre in [('L','l'),('R','r')]:
    for src,dst in [('Shoulder','clavicle'),('UpperArm','upperarm_twist'),('Forearm','foretwist'),('Hand','hand'),('Thigh','thigh'),('Shin','calf'),('Foot','foot'),('Toe','toe0')]:
        mapping[f'{side}_{src}']=f'{pre}_{dst}';landmarks[f'{pre}_{dst}']=f'{side}_{src}'
    mapping[f'{side}_UpperArm_Twist_s1']=f'{pre}_upperarm_twist'
    mapping[f'{side}_UpperArm_Twist_s2']=f'{pre}_upperarm_twist1'
    mapping[f'{side}_Forearm_Twist_s1']=f'{pre}_foretwist'
    mapping[f'{side}_Forearm_Twist_s2']=f'{pre}_foretwist1'
    mapping[f'{side}_Wrist_Twist_s']=f'{pre}_hand'
    mapping[f'{side}_Help_Knee_s']=f'{pre}_calf'
    mapping[f'{side}_Help_Elbow_s']=f'{pre}_foretwist'
for dst,src in landmarks.items():source[ni[dst]]=anatomy[src]
# RE Spine_0 is coincident with Hip. A midpoint supplies a distinct segment
# for geometric fitting without altering the native skeleton rest transforms.
source[ni['spine']]=(anatomy['Hip']+anatomy['Spine_1'])/2
for pre in ['l','r']:
    for mid,a,b in [('upperarm_twist1','upperarm_twist','foretwist'),('foretwist1','foretwist','hand')]:
        source[ni[f'{pre}_{mid}']]=(source[ni[f'{pre}_{a}']]+source[ni[f'{pre}_{b}']])/2
    source[ni[f'{pre}_finger0']]=anatomy[('L' if pre=='l' else 'R')+'_MiddleF1']
    # Every RE digit follows the native hand. No RE face or finger animation is retained.
next_name={'pelvis':'spine','spine':'spine1','spine1':'spine2','spine2':'neck','neck':'head'}
for pre in ['l','r']:
    for a,b in [('thigh','calf'),('calf','foot'),('foot','toe0'),('clavicle','upperarm_twist'),('upperarm_twist','foretwist'),('upperarm_twist1','foretwist'),('foretwist','hand'),('foretwist1','hand'),('hand','finger0')]:next_name[f'{pre}_{a}']=f'{pre}_{b}'
transforms=[]
for i,name in enumerate(names):
    if name not in next_name:transforms.append(np.eye(3));continue
    j=ni[next_name[name]];a=source[j]-source[i];b=target[j]-target[i]
    aa=a/np.linalg.norm(a);bb=b/np.linalg.norm(b);v=np.cross(aa,bb);c=aa@bb
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    transforms.append((np.eye(3)+k+k@k/max(1+c,1e-8))@(np.eye(3)+(np.linalg.norm(b)/np.linalg.norm(a)-1)*np.outer(aa,aa)))
transforms=np.array(transforms)
anchors=[i for i,n in enumerate(names) if not any(t in n for t in ['twist1','finger0'])]
warp=RBFInterpolator(source[anchors][:,[0,2]],target[anchors]-source[anchors],kernel='thin_plate_spline',smoothing=1e-5)
def deform(p):
    out=p+warp(p[:,[0,2]])
    for pre in ['l','r']:
        ids=[ni[pre+'_'+s] for s in ['upperarm_twist','foretwist','hand']]
        distances=[]
        for i in ids:
            end=source[ni[next_name[names[i]]]];axis=end-source[i]
            t=np.clip((p-source[i])@axis/(axis@axis),0,1)
            distances.append(np.linalg.norm(p-source[i]-t[:,None]*axis,axis=1))
        ds=np.stack(distances,axis=1);weights=np.exp(-(ds-ds.min(1,keepdims=True))/.018);weights/=weights.sum(1,keepdims=True)
        fitted=sum(weights[:,j,None]*((p-source[i])@transforms[i].T+target[i]) for j,i in enumerate(ids))
        a=np.clip((np.abs(p[:,0])-.11)/.10,0,1)*np.clip((p[:,2]-.95)/.10,0,1)
        a*=p[:,0]<0 if pre=='l' else p[:,0]>0
        a=a*a*(3-2*a)
        out=out*(1-a[:,None])+fitted*a[:,None]
    # Keep Ada's fixed face proportions. The same spatial field is used across
    # clothing/skin so different source weights cannot open geometric seams.
    h=np.clip((p[:,2]-1.428357)/(.08),0,1);h=h*h*(3-2*h)
    rigid=p+target[ni['head']]-source[ni['head']]
    out=out*(1-h[:,None])+rigid*h[:,None]
    t=np.clip((p[:,2]-.09)/.16,0,1);t=t*t*(3-2*t)
    out[:,2]+=.016*(1-t)
    return out

def native_weights(parsed,sub):
    bones=parsed.skeleton.boneList;by_name={b.boneName:b for b in bones}
    dest=[]
    for name in parsed.skeleton.weightedBones:
        original=name
        if name.startswith(('hair','Facial','L_Cheek','R_Cheek')):name='Head'
        while name not in mapping:
            b=by_name.get(name)
            if b is None or b.parentIndex<0:name='Head' if len(bones)>180 else 'Hip';break
            name=bones[b.parentIndex].boneName
        dest.append(ni[mapping[name]])
    w=np.zeros((len(sub.vertexPosList),len(names)))
    idx=np.asarray(sub.weightIndicesList,dtype=int);rw=np.asarray(sub.weightList,float)
    for j in range(idx.shape[1]):np.add.at(w,(np.arange(len(w)),np.array(dest)[idx[:,j]]),rw[:,j])
    return w/np.maximum(w.sum(1,keepdims=True),1e-12)

def anatomical_weights(p,part):
    def smooth(a,b,x):
        t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
    def segment_weights(ids):
        ds=[]
        for i in ids:
            end=target[ni[next_name[names[i]]]];a=end-target[i]
            t=np.clip((p-target[i])@a/(a@a),0,1)
            ds.append(np.linalg.norm(p-target[i]-t[:,None]*a,axis=1))
        d=np.stack(ds,axis=1);v=np.exp(np.maximum(-(d-d.min(1,keepdims=True))/.018,-30))
        keep=np.argsort(-v,axis=1)[:,:2];mask=np.zeros_like(v);np.put_along_axis(mask,keep,1,1);v*=mask;v/=v.sum(1,keepdims=True)
        w=np.zeros((len(p),len(names)))
        for j,i in enumerate(ids):w[:,i]=v[:,j]
        return w,d.min(1)
    spine=[ni[n] for n in ['pelvis','spine','spine1','spine2','neck','head']]
    z=target[spine,2];interval=np.clip(np.searchsorted(z,p[:,2])-1,0,len(spine)-2)
    a=np.array(spine)[interval];b=np.array(spine)[interval+1]
    t=smooth(target[a,2],target[b,2],p[:,2]);w=np.zeros((len(p),len(names)))
    w[np.arange(len(p)),a]=1-t;w[np.arange(len(p)),b]=t
    if part=='head':return w
    if part=='legs':
        out=np.zeros_like(w)
        for pre in ['l','r']:
            side=p[:,0]<0 if pre=='l' else p[:,0]>=0
            ids=[ni[pre+'_'+s] for s in ['thigh','calf','foot']];out[side]=segment_weights(ids)[0][side]
        return out
    for pre in ['l','r']:
        side=p[:,0]<0 if pre=='l' else p[:,0]>=0
        arm,distance=segment_weights([ni[pre+'_'+s] for s in ['clavicle','upperarm_twist','foretwist','hand']])
        hand=ni[pre+'_hand'];fixed=1-smooth(.04,.09,np.linalg.norm(p-target[hand],axis=1))
        arm*=1-fixed[:,None];arm[:,hand]+=fixed
        amount=smooth(.12,.24,np.abs(p[:,0]))*(1-smooth(.065,.14,distance))*side
        w=w*(1-amount[:,None])+arm*amount[:,None]
    # The short knit hem uses three stable influences, avoiding an abrupt
    # top-four change between pelvis/spine and leg bones across the hip.
    below=p[:,2]<1.02;leg=smooth(.94,.80,p[below,2]);right=smooth(-.035,.035,p[below,0])
    lower=np.zeros((below.sum(),len(names)));lower[:,ni['pelvis']]=1-leg;lower[:,ni['l_thigh']]=leg*(1-right);lower[:,ni['r_thigh']]=leg*right
    amount=1-smooth(.94,1.02,p[below,2]);w[below]=w[below]*(1-amount[:,None])+lower*amount[:,None]
    return w/w.sum(1,keepdims=True)

data={};manifest=[];transfer=[]
skip={'Eyewet_mat','Ao_mat','Eye_out_mat'}
for slot in ['00','10','20']:
    parsed=load_mesh(str(ROOT/f'input/cha800_{slot}.mesh.221108797'))
    raw={}
    for g in parsed.mainMeshLODList[0].visconGroupList:
        for s in g.subMeshList:
            if s.isReusedMesh:continue
            mat=parsed.materialNameList[s.materialIndex]
            raw.setdefault(mat,[]).append((np.array(s.vertexPosList),native_weights(parsed,s)))
    p,uv,n,groups=obj(ROOT/f'input/cha200/cha200_{slot}_lod0.obj')
    for mat,faces in groups.items():
        if mat in skip:continue
        f=np.array(faces);corners=f.reshape(-1,3)
        unique,inv=np.unique(corners,axis=0,return_inverse=True)
        q=p[unique[:,0]];u=uv[unique[:,1]];normal=n[unique[:,2]]@C.T
        candidates=raw.get(mat,[x for rows in raw.values() for x in rows])
        rp=np.concatenate([x[0] for x in candidates]);rw=np.concatenate([x[1] for x in candidates])
        distance,near=cKDTree(rp).query(q);w=rw[near].copy()
        if slot=='20':w[:]=0;w[:,ni['head']]=1
        if slot=='10':
            # Neck uses exactly the same continuous neck/head influence field as
            # body skin; eyes, eyebrows, mouth and upper face remain fixed to head.
            w[:]=0;h=np.clip((q[:,1]-1.428357)/(1.554219-1.428357),0,1)
            if mat!='Face_mat':h[:]=1
            w[:,ni['head']]=h;w[:,ni['neck']]=1-h
        if mat in ['Skin_Mat','Knit_Mat']:
            neck=q[:,1]>1.428357
            h=np.clip((q[neck,1]-1.428357)/(1.554219-1.428357),0,1)
            w[neck]=0;w[neck,ni['head']]=h;w[neck,ni['neck']]=1-h
        # Keep at most four native influences before fitting and exporting.
        keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True)
        original_weight=w.copy();converted=q@C.T;fitted=deform(converted)
        # Transform corner normals through the local deformation Jacobian.
        jac=np.stack([(deform(converted+np.eye(3)[i]*1e-4)-fitted)/1e-4 for i in range(3)],axis=2)
        normal_fit=np.linalg.solve(jac.transpose(0,2,1),normal[:,:,None])[:,:,0]
        normal_fit/=np.maximum(np.linalg.norm(normal_fit,axis=1,keepdims=True),1e-12)
        part='head' if slot!='00' else ('gloves' if mat=='Glove_Mat' else ('legs' if mat.startswith('Boots') else 'body'))
        if part=='gloves':
            for pre in ['l','r']:
                side=converted[:,0]<0 if pre=='l' else converted[:,0]>0;i=ni[pre+'_hand']
                rotation=transforms[i];u1,s1,v1=np.linalg.svd(rotation);rotation=u1@v1
                fitted[side]=(converted[side]-source[i])@rotation.T+target[i];normal_fit[side]=normal[side]@rotation.T
            w[:]=0;w[converted[:,0]<0,ni['l_hand']]=1;w[converted[:,0]>0,ni['r_hand']]=1
        elif slot=='00' and mat in ['Gun_Mat','HookGun_Mat','HolsterMetal_Mat','BeltHolster_Metal_Mat']:
            # Rigid hardware and leather holsters use uniform weights per connected
            # piece. Weld the OBJ corner splits for connectivity only.
            coords,owners=np.unique(np.round(converted,6),axis=0,return_inverse=True)
            tri=owners[inv.reshape(-1,3)];edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])
            graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(coords),len(coords)))
            count,labels=connected_components(graph,directed=False);component=labels[owners]
            w[:]=0
            for c in range(count):
                select=component==c;center=fitted[select].mean(0)
                # Keep the same rest-shape warp as the neighboring garment.
                # Uniform motion weights prevent buckles stretching in poses.
                piece=anatomical_weights(center[None],'legs' if mat.startswith('Boots') else 'body')[0]
                # Uniform component influences follow the garment attachment
                # frame without elastic deformation inside a metal buckle.
                w[select]=piece
        elif slot=='00':
            # Original mapping is a reference; the final anatomical rebind
            # eliminates RE helper/physics-chain artifacts at shoulders/knees.
            w=anatomical_weights(fitted,part)
        elif slot=='10' and mat=='Face_mat':w=anatomical_weights(fitted,'head')
        keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True)
        name='reada_'+part+'_'+mat.lower().replace('_mat','')
        data[name+'_p']=fitted.astype('f4');data[name+'_n']=normal_fit.astype('f4');data[name+'_uv']=u.astype('f4');data[name+'_w']=w.astype('f4');data[name+'_f']=inv.reshape(-1,3).astype('i4')
        rec={'object':name,'part':part,'material':mat,'slot':slot,'vertices':len(q),'triangles':len(f),'kind':'hair' if slot=='20' else ('face' if slot=='10' else 'cloth')}
        manifest.append(rec);transfer.append(dict(material=mat,max_distance=float(distance.max()),p99_distance=float(np.quantile(distance,.99)),mean_distance=float(distance.mean())))
# Matching duplicated attachment positions must preserve identical coordinates,
# normals and weights. Matching only compatible material families excludes hair.
bucket={}
for rec in manifest:
    if rec['kind']=='hair':continue
    name=rec['object']
    for i,p in enumerate(data[name+'_p']):bucket.setdefault(tuple(np.round(p,5)),[]).append((name,i))
shared=0
for refs in bucket.values():
    if len({name for name,i in refs})<2:continue
    w=np.mean([data[name+'_w'][i] for name,i in refs],axis=0)
    p=np.mean([data[name+'_p'][i] for name,i in refs],axis=0)
    normal=np.mean([data[name+'_n'][i] for name,i in refs],axis=0);normal/=max(np.linalg.norm(normal),1e-12)
    for name,i in refs:data[name+'_p'][i]=p;data[name+'_w'][i]=w;data[name+'_n'][i]=normal
    shared+=1
np.savez_compressed(ROOT/'build/fitted_model.npz',**data)
(ROOT/'build/manifest.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'reports/weight_transfer.json').write_text(json.dumps({'source':'cha200 OBJ appearance, cha800 original per-material weights','native_bones':names,'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'coordinate_rotation':C.tolist(),'materials':transfer,'matched_attachment_positions':shared,'facial_animation':False,'custom_body_compatibility':False,'final_skinning':'Native anatomical rebind informed by original anatomy and per-material RE weight correspondence checks. Fixed face and hands.','rigid_hardware':'Uniform native influences per connected component','shoe_floor_correction_m':.016},indent=2))
originals={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'input').rglob('*') if p.is_file()}
(ROOT/'reports/input_hashes.json').write_text(json.dumps(originals,indent=2))
print('MODEL_PREPARED',len(manifest),'groups')
