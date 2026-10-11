"""Whole-body race mesh: uniform units/orientation only, no anatomy reshaping."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[1];WS=R.parents[1]
sys.path.insert(0,str(R/'tools'))
from finger_rig import extend, skin_weights
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
data=json.loads((R/'reports/human_skeleton.json').read_text())
native=parse_skeljson(data);n=native['boneCount'];assert n==28
cfg=json.loads((R/'tools/model_config.json').read_text());U=cfg['unit_scale'];K=U/.01
names=[name+'_'+str(i) for i,name in enumerate(native['names'])]
# Anatomical pivots measured in the original model's centimetre coordinates.
# They affect skinning only: every source vertex is kept at its original ratio.
landmarks={0:[0,0,75],1:[-7.5,0,75],2:[-9,0,41],3:[-10,-1,7],4:[-10,6,1],5:[7.5,0,75],6:[9,0,41],7:[10,-1,7],8:[10,6,1],9:[0,0,85],10:[0,0,97],11:[0,0,106],12:[0,0,114],13:[0,0,121],14:[-4,0,109],15:[-13,0,107],17:[-27,0,92],19:[-38,0,82],20:[-42,0,77],21:[4,0,109],22:[13,0,107],24:[27,0,92],26:[38,0,82],27:[42,0,77]}
S=np.zeros((n,3))
for i,sign in [(19,-1),(26,1)]:
    wrist=np.array(cfg['hand_rig']['wrist_cm']);wrist[0]*=sign;landmarks[i]=wrist.tolist()
for i,p in landmarks.items():S[i]=np.array(p)*U
for i,a,b in [(16,15,17),(18,17,19),(23,22,24),(25,24,26)]:S[i]=(S[a]+S[b])/2
world=native['restWorld'].copy();world[:,:3,3]=S
local=np.array([world[i] if p<0 else np.linalg.inv(world[p])@world[i] for i,p in enumerate(native['parent'])])
bones=[]
for i,b in enumerate(data['bones']):
    raw=np.array(b['rest']).reshape(4,4).T
    raw[:3,:3]=local[i,:3,:3];raw[:3,3]=local[i,:3,3]
    bones.append(dict(name=b['name'],parent=b['parent'],rest=raw.T.reshape(-1).tolist()))
world, extended_parents, extended_names, finger_rows, finger_segments = extend(world, native['parent'], native['names'])
names=[name+'_'+str(i) for i,name in enumerate(extended_names)]
for i in range(28, len(world)):
    parent=int(extended_parents[i]); raw=np.array(data['bones'][26]['rest']).reshape(4,4).T.copy()
    frame=np.linalg.inv(world[parent])@world[i]
    raw[:3,:3]=frame[:3,:3];raw[:3,3]=frame[:3,3]
    bones.append(dict(name=extended_names[i],parent=parent,rest=raw.T.reshape(-1).tolist()))
(R/'build/skeleton_spec.json').write_text(json.dumps(bones,indent=2))
(R/'reports/finger_rig_layout.json').write_text(json.dumps(dict(version=cfg['version'],bones=58,added_joints=finger_rows,game_verified=False),indent=2))
nextbone={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,16:17,17:19,18:19,19:20,21:22,22:24,23:24,24:26,25:26,26:27}
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def near(p,ids):
    ds=[]
    for i in ids:
        a=S[i]/K;b=S[nextbone[i]]/K if i in nextbone else a+(a-S[native['parent'][i]]/K)*.5
        v=b-a;t=np.clip((p-a)@v/max(v@v,1e-10),0,1)
        ds.append(np.linalg.norm(p-a-t[:,None]*v,axis=1))
    ds=np.array(ds).T;v=np.exp(np.maximum(-(ds-ds.min(1,keepdims=True))/.025,-30));w=np.zeros((len(p),n));w[:,ids]=v
    return w/w.sum(1,keepdims=True)
def weights(p,head=False,allow_arms=True,hands=False):
    if head:
        w=np.zeros((len(p),n));w[:,13]=1;return w
    if hands:
        w=np.zeros((len(p),n))
        for sign,hand,twist in [(-1,19,18),(1,26,25)]:
            ix=np.where(p[:,0]*sign>=0)[0];u=(p[ix]-S[hand]/K)@world[hand,:3,0]
            h=smooth(*cfg['hand_rig']['wrist_blend_m'],u);w[ix,hand]=h;w[ix,twist]=1-h
        return w
    w=near(p,[0,9,10,11,12]);lo=1-smooth(.72,.84,p[:,2]);side=smooth(-.025,.025,p[:,0])
    legs=near(p,[0,1,2,3])*(1-side[:,None])+near(p,[0,5,6,7])*side[:,None]
    w=w*(1-lo[:,None])+legs*lo[:,None]
    if allow_arms:
        for sign,ids in [(-1,[14,15,17,19]),(1,[21,22,24,26])]:
            ix=np.where(p[:,0]*sign>=0)[0];q=p[ix];a=smooth(.08,.16,abs(q[:,0]))*smooth(.68,.74,q[:,2])
            w[ix]=w[ix]*(1-a[:,None])+near(q,ids)*a[:,None]
    h=smooth(1.12,1.18,p[:,2]);w*=1-h[:,None];w[:,13]+=h
    if allow_arms:
        for sign,fore,twist,hand in [(-1,17,18,19),(1,24,25,26)]:
            ix=np.where((p[:,0]*sign>.29)&(p[:,2]>.76))[0];q=p[ix]-S[hand]/K
            u=q@world[hand,:3,0];distance=np.linalg.norm(q-u[:,None]*world[hand,:3,0],axis=1)
            blend=smooth(-.13,-.075,u)*(1-smooth(.045,.075,distance));h=smooth(*cfg['hand_rig']['wrist_blend_m'],u);t=smooth(-.105,-.030,u)
            refined=np.zeros((len(ix),n));refined[:,fore]=(1-h)*(1-t);refined[:,twist]=(1-h)*t;refined[:,hand]=h
            w[ix]=w[ix]*(1-blend[:,None])+refined*blend[:,None]
    ix=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,ix,1,1);w*=mask
    return w/w.sum(1,keepdims=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
parts=json.loads((R/'input/parts.json').read_text());manifest=[];arrays={};maxerr=0
for row in parts:
    ob=bpy.data.objects[row['name']];raw=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);p=raw*np.array(cfg['orientation'])*U
    for v,co in zip(ob.data.vertices,p):v.co=co
    ob.matrix_world=Matrix.Identity(4)
    head=row['tex'] in ['eye_D','face_D','eyelash_D','hair_D','head_D']
    w=weights(p/K,head,allow_arms=row['name'] in ['mesh_02_153203','mesh_07_535767','mesh_09_689493'],hands=row['name']=='mesh_04_281363')
    w=skin_weights(p,w,finger_segments) if row['name']=='mesh_04_281363' else np.pad(w,((0,0),(0,30)))
    if len(manifest)==8:w[:]=0;w[:,0]=1
    for i,name in enumerate(names):
        group=ob.vertex_groups.new(name=name)
        for vi in np.where(w[:,i]>0)[0]:group.add([int(vi)],float(w[vi,i]),'REPLACE')
    index=len(manifest);ob.name=f'wdr_part_{index:02d}'
    if ob.name in cfg['uv_flip_v_parts']:
        for loop in ob.data.uv_layers.active.data:loop.uv.y=1-loop.uv.y
    if ob.name=='wdr_part_04':
        for face in ob.data.polygons:face.use_smooth=True
    manifest.append(dict(object=ob.name,source_object=row['name'],texture=row['tex']+'.png',material='wdr_mat_'+row['tex'],cutout=row['alpha']))
    arrays[ob.name+'_p']=p;maxerr=max(maxerr,float(abs(p-raw*np.array(cfg['orientation'])*U).max()))
# Component-aware cloth distances: fixed garment roots, mobile hanging ends.
cloth_rows=[]
for row in manifest:
    if row['object'] not in cfg['cloth_parts']:continue
    ob=bpy.data.objects[row['object']];me=ob.data;p=np.array([v.co[:] for v in me.vertices]);q=p/K
    parents=list(range(len(p)))
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    def join(a,b):
        a=root(a);b=root(b)
        if a!=b:parents[b]=a
    identical={}
    for i,pos in enumerate(q):
        key=tuple(np.round(pos,5))
        if key in identical:join(i,identical[key])
        else:identical[key]=i
    for poly in me.polygons:
        for i in poly.vertices[1:]:join(poly.vertices[0],i)
    comps={}
    for i in range(len(p)):comps.setdefault(root(i),[]).append(i)
    alpha=np.zeros(len(p));kind=cfg['cloth_parts'][row['object']]
    for ids in comps.values():
        ids=np.array(ids);z=q[ids,2];x=abs(q[ids,0]);span=np.ptp(z)
        if len(ids)<12:continue
        if kind=='skirt' and span>.25:
            travel=1-smooth(z.max()-.065,z.max()-.025,z)
        elif kind=='sleeve' and len(ids)>80 and x.min()>.07:
            travel=smooth(x.min()+.025,x.max(),x)
        elif kind=='cuff' and len(ids)>100:
            travel=1-smooth(z.max()-.035,z.max()-.012,z)
        elif kind=='hair' and span>.06:
            travel=1-smooth(z.max()-.055,z.max()-.02,z)
            # Scalp and face-framing hair follow the head rigidly. Height-only
            # component roots allowed these close-fitting cards to sink inward.
            travel*=1-smooth(*cfg['hair_root_band_m'],z)
        else:continue
        # Ensure each selected component has an explicit root before cooking.
        travel[z>=z.max()-.008]=0
        alpha[ids]=travel*cfg['cloth_max_distance_m'][kind]
        if kind=='skirt':alpha[ids]+=cfg['skirt_root_extra_m']*smooth(0,.04,travel)*(1-smooth(.10,.20,travel))
    layer=me.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
    for i,a in enumerate(alpha):layer.data[i].color=(1,1,1,float(a))
    cloth_rows.append(dict(object=ob.name,kind=kind,active=int(np.sum(alpha>0)),fixed=int(np.sum(alpha==0)),max_distance_m=float(alpha.max())))
(R/'reports/cloth_source.json').write_text(json.dumps(cloth_rows,indent=2))

for image in bpy.data.images:
    if image.source=='FILE':
        path=R/'tex'/(image.name.split('.png')[0]+'.png')
        if path.exists():image.filepath=str(path);image.reload();image.pack()
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name='wdr_skeleton'
bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0])
for i,name in enumerate(names):
    b=arm.data.edit_bones.new(name);b.length=.025;b.matrix=Matrix(world[i].tolist())
for i,name in enumerate(names):
    if extended_parents[i]>=0:arm.data.edit_bones[name].parent=arm.data.edit_bones[names[extended_parents[i]]]
    if i>=28:
        arm.data.edit_bones[name].length=float(np.linalg.norm(np.array(finger_rows[i-28]['tail'])-world[i,:3,3]))
bpy.ops.object.mode_set(mode='OBJECT')
for row in manifest:
    ob=bpy.data.objects[row['object']];mod=ob.modifiers.new('Race binding','ARMATURE');mod.object=arm;ob.parent=arm
arm['finger_controls']='Rotate local X on l/r_thumb/index/middle/ring/little_1/2/3; positive closes the hand. Game driver: FingerController.'
allp=np.concatenate(list(arrays.values()));report=dict(unit_scale=U,uniform_orientation=cfg['orientation'],source_geometry_max_error_m=maxerr,total_height_m=float(np.ptp(allp[:,2])),vertices=len(allp),source_proportions_preserved=True,custom_skeleton=True,bones=58,finger_joints=30,engine_verified=False,cloth_enabled=True)
(R/'build/rig_manifest.json').write_text(json.dumps(manifest,indent=2));np.savez_compressed(R/'build/source_positions.npz',**arrays)
(R/'reports/source_validation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/WuduCanglan_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='RELATIVE')
print('RIG_READY',json.dumps(report))
