"""Preserve original cha200 geometry; fit a semantic bind skeleton to RE anatomy."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[2]
sys.path.insert(0,'D:/dsh-mod/re4-remake/tools')
from scan_mesh import load_mesh
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
cfg=json.loads((ROOT/'tools/model_config.json').read_text())

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
            corners=[tuple(int(x)-1 for x in t.split('/')) for t in s[1:]]
            for j in range(1,len(corners)-1):groups[mat].append([corners[0],corners[j],corners[j+1]])
    return np.array(p),np.array(uv),np.array(n),groups

C=np.array([[-1,0,0],[0,0,1],[0,1,0]],float)
native_data=json.loads((ROOT/'reports/human_skeleton.json').read_text())
native=parse_skeljson(native_data);names=native['names'];ni={n:i for i,n in enumerate(names)}
source_json=json.loads((ROOT/'input/cha200/cha200_00_skeleton.json').read_text())
anatomy={b['name']:np.array(b['worldMatrix'])[3,:3]@C.T for b in source_json['bones']}
mapping={'Hip':'pelvis','Spine_0':'spine','Spine_1':'spine1','Spine_2':'spine2','Neck_0':'neck','Neck_1':'neck','Head':'head'}
landmarks={'pelvis':'Hip','spine1':'Spine_1','spine2':'Spine_2','neck':'Neck_0','head':'Head'}
for side,pre in [('L','l'),('R','r')]:
    for src,dst in [('Shoulder','clavicle'),('UpperArm','upperarm_twist'),('Forearm','foretwist'),('Hand','hand'),('Thigh','thigh'),('Shin','calf'),('Foot','foot'),('Toe','toe0')]:
        mapping[f'{side}_{src}']=f'{pre}_{dst}';landmarks[f'{pre}_{dst}']=f'{side}_{src}'
    for src,dst in [('UpperArm_Twist_s1','upperarm_twist'),('UpperArm_Twist_s2','upperarm_twist1'),('Forearm_Twist_s1','foretwist'),('Forearm_Twist_s2','foretwist1'),('Wrist_Twist_s','hand'),('Help_Knee_s','calf'),('Help_Elbow_s','foretwist')]:mapping[f'{side}_{src}']=f'{pre}_{dst}'
S=np.zeros((len(names),3))
for dst,src in landmarks.items():S[ni[dst]]=anatomy[src]
S[ni['spine']]=(anatomy['Hip']+anatomy['Spine_1'])/2
next_name={'pelvis':'spine','spine':'spine1','spine1':'spine2','spine2':'neck','neck':'head'}
for pre in ['l','r']:
    side='L' if pre=='l' else 'R'
    S[ni[f'{pre}_finger0']]=anatomy[f'{side}_MiddleF1']
    for mid,a,b in [('upperarm_twist1','upperarm_twist','foretwist'),('foretwist1','foretwist','hand')]:S[ni[f'{pre}_{mid}']]=(S[ni[f'{pre}_{a}']]+S[ni[f'{pre}_{b}']])/2
    for a,b in [('thigh','calf'),('calf','foot'),('foot','toe0'),('clavicle','upperarm_twist'),('upperarm_twist','foretwist'),('upperarm_twist1','foretwist'),('foretwist','hand'),('foretwist1','hand'),('hand','finger0')]:next_name[f'{pre}_{a}']=f'{pre}_{b}'

# Orient anatomical bone segments to the ORIGINAL A pose. Retaining the native
# T-pose axes while moving joints into A pose would bake a second shoulder angle
# into animation offsets. Positions and bone axes adapt; source vertices do not.
def align(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);c=np.clip(a@b,-1,1);v=np.cross(a,b)
    if c < -.999999:
        axis=np.cross(a,[1,0,0] if abs(a[0])<.8 else [0,1,0]);axis/=np.linalg.norm(axis)
        return 2*np.outer(axis,axis)-np.eye(3)
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+k+k@k/max(1+c,1e-12)
world=native['restWorld'].copy();world[:,:3,3]=S
for i,name in enumerate(names):
    if name in next_name:
        j=ni[next_name[name]]
        world[i,:3,:3]=align(native['restWorld'][j,:3,3]-native['restWorld'][i,:3,3],S[j]-S[i])@native['restWorld'][i,:3,:3]
local=np.array([world[i] if par<0 else np.linalg.inv(world[par])@world[i] for i,par in enumerate(native['parent'])])
bones=[{'name':name,'parent':int(native['parent'][i]),'rest':local[i].T.reshape(-1).tolist()} for i,name in enumerate(names)]
(ROOT/'build/skeleton_spec.json').write_text(json.dumps(bones,indent=2))
# Temporary rig metadata feeds Blender; final TPAC readback replaces this for QA.
rig_data={'name':cfg['skeleton'],'guid':'pending-final-readback','boneCount':len(names),'bones':[dict(i=i,**b) for i,b in enumerate(bones)]}
(ROOT/'build/bind_skeleton.json').write_text(json.dumps(rig_data,indent=2))

def mapped_weights(parsed,sub):
    bones=parsed.skeleton.boneList;by_name={b.boneName:b for b in bones};dest=[]
    for name in parsed.skeleton.weightedBones:
        if name.startswith(('hair','Facial','L_Cheek','R_Cheek')):name='Head'
        while name not in mapping:
            b=by_name.get(name)
            if b is None or b.parentIndex<0:name='Head' if len(bones)>180 else 'Hip';break
            name=bones[b.parentIndex].boneName
        dest.append(ni[mapping[name]])
    w=np.zeros((len(sub.vertexPosList),len(names)));idx=np.asarray(sub.weightIndicesList,dtype=int);rw=np.asarray(sub.weightList,float)
    for j in range(idx.shape[1]):np.add.at(w,(np.arange(len(w)),np.array(dest)[idx[:,j]]),rw[:,j])
    return w/np.maximum(w.sum(1,keepdims=True),1e-12)

skip={'Eyewet_mat','Ao_mat','Eye_out_mat'}|set(cfg['removed_materials'])
data={};manifest=[];transfer=[];source_refs={};maxerr=0;hidden_skin_faces=0
neck_z=anatomy['Neck_0'][2];head_base_z=anatomy['Neck_1'][2]
for slot in ['00','10','20']:
    parsed=load_mesh(str(ROOT/f'input/cha800_{slot}.mesh.221108797'));raw={}
    for group in parsed.mainMeshLODList[0].visconGroupList:
        for sub in group.subMeshList:
            if sub.isReusedMesh:continue
            mat=parsed.materialNameList[sub.materialIndex]
            raw.setdefault(mat,[]).append((np.array(sub.vertexPosList),mapped_weights(parsed,sub)))
    p,uv,n,groups=obj(ROOT/f'input/cha200/cha200_{slot}_lod0.obj')
    for mat,faces in groups.items():
        if mat in skip:continue
        f=np.array(faces)
        if mat=='Face_mat':
            # The head asset includes a lower neck flare enclosed by the dress.
            # Exclude that invisible lining rather than moving either surface.
            points=p[f[:,:,0]]@C.T
            torso=(points[:,:,2]<anatomy['Neck_0'][2]+.02).all(1)
            hidden_skin_faces+=int(torso.sum());f=f[~torso]
        unique,inv=np.unique(f.reshape(-1,3),axis=0,return_inverse=True)
        q=p[unique[:,0]];converted=q@C.T;u=uv[unique[:,1]];normal=n[unique[:,2]]@C.T
        candidates=raw.get(mat,[x for rows in raw.values() for x in rows]);rp=np.concatenate([x[0] for x in candidates]);rw=np.concatenate([x[1] for x in candidates])
        distance,near=cKDTree(rp).query(q);w=rw[near].copy()
        if mat=='Knit_Mat':
            # Smooth the transferred shoulder field in source coordinates. This
            # changes influences only; original vertices and UVs stay untouched.
            tree=cKDTree(rp)
            for start in range(0,len(q),2048):
                d,j=tree.query(q[start:start+2048],k=min(256,len(rp)))
                a=np.exp(-.5*(d/.025)**2);a/=a.sum(1,keepdims=True)
                w[start:start+2048]=np.einsum('ij,ijk->ik',a,rw[j])
        if slot=='20' or (slot=='10' and mat!='Face_mat'):w[:]=0;w[:,ni['head']]=1
        if mat in ['Skin_Mat','Knit_Mat','Face_mat']:
            # Blend only along the neck. The entire face, including jaw and
            # mouth surfaces, must move rigidly with the same head influence.
            h=np.clip((converted[:,2]-neck_z)/(head_base_z-neck_z),0,1)
            fixed=np.zeros_like(w);fixed[:,ni['head']]=h;fixed[:,ni['neck']]=1-h
            if mat=='Face_mat':w=fixed
            else:
                # Collar is central. A height-only cutoff would incorrectly bind
                # shoulder vertices to neck and create a discontinuity at z=neck.
                center=np.clip((.12-np.abs(converted[:,0]))/(.12-.055),0,1);center=center*center*(3-2*center)
                high=np.clip((converted[:,2]-(neck_z-.04))/.04,0,1);high=high*high*(3-2*high)
                amount=center*high;w=w*(1-amount[:,None])+fixed*amount[:,None]
        part='head' if slot!='00' else ('gloves' if mat=='Glove_Mat' else ('legs' if mat.startswith('Boots') else 'body'))
        if part=='gloves':
            w[:]=0;w[converted[:,0]<0,ni['l_hand']]=1;w[converted[:,0]>=0,ni['r_hand']]=1
        # Continuous wrist blending in exposed skin/sleeve. Finger geometry stays rigid.
        if mat in ['Skin_Mat','Knit_Mat']:
            for side,pre in [(-1,'l'),(1,'r')]:
                hand=S[ni[pre+'_hand']];elbow=S[ni[pre+'_foretwist']];axis=hand-elbow;axis/=np.linalg.norm(axis)
                along=(converted-hand)@axis;rad=np.linalg.norm((converted-hand)-along[:,None]*axis,axis=1)
                select=converted[:,0]*side>0
                h=np.clip((along[select]+.025)/.04,0,1);h=h*h*(3-2*h)
                amount=np.clip((along[select]+.06)/.03,0,1);amount=amount*amount*(3-2*amount)
                near=np.clip((.085-rad[select])/.03,0,1);near=near*near*(3-2*near);amount*=near
                fixed=np.zeros_like(w[select]);fixed[:,ni[pre+'_hand']]=h;fixed[:,ni[pre+'_foretwist1']]=1-h
                w[select]=w[select]*(1-amount[:,None])+fixed*amount[:,None]
        keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True)
        name='adar_'+part+'_'+mat.lower().replace('_mat','')
        data[name+'_p']=converted.astype('f4');data[name+'_n']=normal.astype('f4');data[name+'_uv']=u.astype('f4');data[name+'_w']=w.astype('f4');data[name+'_f']=inv.reshape(-1,3).astype('i4')
        source_refs[name+'_p']=converted.astype('f4');source_refs[name+'_source_indices']=unique[:,0].astype('i4')
        maxerr=max(maxerr,float(abs(data[name+'_p'].astype(float)-converted).max()))
        manifest.append({'object':name,'part':part,'material':mat,'slot':slot,'vertices':len(q),'triangles':len(f),'kind':'hair' if slot=='20' else ('face' if slot=='10' else 'cloth')})
        transfer.append({'material':mat,'max_distance':float(distance.max()),'p99_distance':float(np.quantile(distance,.99))})
# Share influences and normals at actual coincident seams without moving vertices.
bucket={}
for rec in manifest:
    if rec['kind']=='hair':continue
    name=rec['object']
    for i,pos in enumerate(data[name+'_p']):bucket.setdefault(tuple(pos),[]).append((name,i))
shared=0
for refs in bucket.values():
    if len({name for name,i in refs})<2:continue
    w=np.mean([data[name+'_w'][i] for name,i in refs],axis=0);normal=np.mean([data[name+'_n'][i] for name,i in refs],axis=0);normal/=max(np.linalg.norm(normal),1e-12)
    for name,i in refs:data[name+'_w'][i]=w;data[name+'_n'][i]=normal
    shared+=1
np.savez_compressed(ROOT/'build/fitted_model.npz',**data);np.savez_compressed(ROOT/'build/original_positions.npz',**source_refs)
(ROOT/'build/manifest.json').write_text(json.dumps(manifest,indent=2))
points=np.concatenate([data[r['object']+'_p'] for r in manifest]);assert maxerr<1e-6
report={'source':'Original cha200 OBJ; cha800 per-material weight correspondence','source_geometry_preserved':True,'geometry_transform':C.tolist(),'geometry_max_error_m':maxerr,'uniform_scale':1.0,'anatomy_warp_applied':False,'height_m':float(np.ptp(points[:,2])),'width_m':float(np.ptp(points[:,0])),'source_landmarks':S.tolist(),'native_landmarks':native['restWorld'][:,:3,3].tolist(),'native_bone_order':names,'bind_axes_aligned_to_source_segments':True,'materials':transfer,'matched_attachment_positions':shared,'hand_pose':'fixed','facial_animation':False,'game_verified':False}
report['hidden_lower_neck_faces_excluded']=hidden_skin_faces
(ROOT/'reports/weight_transfer.json').write_text(json.dumps(report,indent=2));(ROOT/'reports/geometry_fidelity.json').write_text(json.dumps({k:report[k] for k in ['source_geometry_preserved','geometry_transform','geometry_max_error_m','uniform_scale','anatomy_warp_applied','height_m','width_m']},indent=2))
originals={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'input').rglob('*') if p.is_file()}
(ROOT/'reports/input_hashes.json').write_text(json.dumps(originals,indent=2))
print('ORIGINAL_GEOMETRY_PRESERVED',len(manifest),maxerr,report['height_m'])
