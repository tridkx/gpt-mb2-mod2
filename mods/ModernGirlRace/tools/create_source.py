"""Bind six source parts without changing their relative geometry or UVs."""
import bpy,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[1];W=R.parents[1]
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
cfg=json.loads((R/'tools/model_config.json').read_text());raw=json.loads((R/'reports/human_skeleton.json').read_text());rig=parse_skeljson(raw)
S=np.array(cfg['landmarks_m']);world=rig['restWorld'].copy();world[:,:3,3]=S
alignment=[]
if cfg.get('align_arm_bind_axes'):
    # Transport each native arm frame to this model's shoulder/elbow/wrist axis.
    # The shortest rotation preserves roll and leaves mesh, joints and weights intact.
    for i,start,end in [(15,15,17),(16,15,17),(17,17,19),(18,17,19),
                        (22,22,24),(23,22,24),(24,24,26),(25,24,26)]:
        a=world[i,:3,0].copy();a/=np.linalg.norm(a)
        v=S[end]-S[start];v/=np.linalg.norm(v)
        cross=np.cross(a,v);c=float(a@v);assert c>-.99
        K=np.array([[0,-cross[2],cross[1]],[cross[2],0,-cross[0]],[-cross[1],cross[0],0]])
        Q=np.eye(3)+K+K@K/(1+c)
        world[i,:3,:3]=Q@world[i,:3,:3]
        alignment.append(dict(bone=rig['names'][i],rotation_degrees=float(np.degrees(np.arccos(np.clip(c,-1,1))))))
(R/'reports/arm_bind_alignment.json').write_text(json.dumps(dict(enabled=bool(cfg.get('align_arm_bind_axes')),bones=alignment,joint_positions_unchanged=True),indent=2))
local=np.array([world[i] if p<0 else np.linalg.inv(world[p])@world[i] for i,p in enumerate(rig['parent'])])
bones=[dict(name=b['name'],parent=b['parent'],rest=local[i].T.reshape(-1).tolist()) for i,b in enumerate(raw['bones'])]
(R/'build/skeleton_spec.json').write_text(json.dumps(bones,indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
objects=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name);assert len(objects)==6
rot=np.array(cfg['source_rotation']);scale=cfg['source_scale'];positions={};weights={};normaldata={}
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
nextbone={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,17:19,19:20,21:22,22:24,24:26,26:27}
def near(p,ids,width=.035):
    # Interpolate adjacent joint transforms along the closest chain segment.
    # At segment ends the shared joint has unit weight, avoiding ranking cuts.
    ds=[];ts=[]
    for i,j in zip(ids[:-1],ids[1:]):
        a=S[i];v=S[j]-a;t=np.clip((p-a)@v/max(v@v,1e-10),0,1)
        ds.append(np.linalg.norm(p-a-t[:,None]*v,axis=1));ts.append(t)
    seg=np.argmin(np.array(ds).T,axis=1);t=np.array(ts).T[np.arange(len(p)),seg];t=t*t*(3-2*t)
    w=np.zeros((len(p),28));ii=np.array(ids)
    w[np.arange(len(p)),ii[seg]]=1-t;w[np.arange(len(p)),ii[seg+1]]=t
    return w
for oi,o in enumerate(objects):
    p=np.array([o.matrix_world@v.co for v in o.data.vertices])@rot.T*scale;positions[o.name]=p
    # Retain supplied corner normals under the same rigid coordinate change.
    normaldata[o.name]=np.array([o.matrix_world.to_3x3()@n.vector for n in o.data.corner_normals])@rot.T
    q=p/scale;z=q[:,2];side=smooth(-.025,.025,q[:,0])
    torso=near(p,[0,9,10,11,12]);legs=np.zeros((len(p),28))
    # Crotch vertices need a continuous pelvis transition; closest-segment
    # selection switches abruptly between the lateral hip and thigh segments.
    knee=smooth(.275,.375,z);ankle=1-smooth(.025,.085,z);pelvis=smooth(.50,.605,z)
    for fraction,thigh,calf,foot in [(1-side,1,2,3),(side,5,6,7)]:
        legs[:,thigh]+=fraction*knee*(1-pelvis)
        legs[:,calf]+=fraction*(1-knee)*(1-ankle)*(1-pelvis)
        legs[:,foot]+=fraction*(1-knee)*ankle*(1-pelvis)
    legs[:,0]=pelvis
    lo=1-smooth(.60,.655,z);w=torso*(1-lo[:,None])+legs*lo[:,None]
    if oi==0:w[:]=0;w[:,13]=1
    elif oi==1:
        h=smooth(.795,.825,z);w=near(p,[11,12,13]);w*=1-h[:,None];w[:,13]+=h
    elif oi in [2,3,4]:
        for sign,ids,hand in [(-1,[14,15,17,19],19),(1,[21,22,24,26],26)]:
            ix=np.where(q[:,0]*sign>=0)[0]
            a=np.ones(len(ix)) if oi in [3,4] else smooth(.06,.14,abs(q[ix,0]))*smooth(.685,.73,z[ix])
            arm=np.zeros((len(ix),28));elbow=1-smooth(.59,.67,z[ix]);h=1-smooth(.502,.54,z[ix])
            arm[:,ids[1]]=1-elbow;arm[:,ids[2]]=elbow*(1-h);arm[:,hand]=elbow*h
            w[ix]=w[ix]*(1-a[:,None])+arm*a[:,None]
    elif oi==5:
        # Shoes and feet move as single native foot bones, with ankle blending.
        foot=1-smooth(.043,.075,z);f=np.zeros_like(w);f[:,3]=1-side;f[:,7]=side;w=w*(1-foot[:,None])+f*foot[:,None]
    weights[o.name]=w
# The six-part source has open sleeve cuts that are close to, but not exactly
# coincident with, the skin cuts. Transfer attachment weights in a local band.
from mathutils.kdtree import KDTree
arm_p=[];arm_w=[]
for o in objects[3:5]:
    p=positions[o.name];selected=p[:,2]>scale*.70
    arm_p.extend(p[selected]);arm_w.extend(weights[o.name][selected])
arm_p=np.array(arm_p);arm_w=np.array(arm_w);tree=KDTree(len(arm_p))
for i,p in enumerate(arm_p):tree.insert(p,i)
tree.balance();upper=objects[2];p=positions[upper.name];w=weights[upper.name]
# Keep the waist attachment on its original shared lower-body weights.
waist_points={tuple(q) for q in np.round(positions[objects[5].name],5)}
for i,co in enumerate(p):
    if tuple(np.round(co,5)) in waist_points:continue
    _,nearest,dist=tree.find(co);a=1-smooth(.008,.10,dist)
    w[i]=w[i]*(1-a)+arm_w[nearest]*a
weights[upper.name]=w
# Matching source cut coordinates share one weight vector across all pieces.
pts=np.concatenate(list(positions.values()));ww=np.concatenate(list(weights.values()));unique,owner=np.unique(np.round(pts,5),axis=0,return_inverse=True)
avg=np.zeros((len(unique),28));np.add.at(avg,owner,ww);avg/=np.bincount(owner)[:,None];ww=avg[owner]
keep=np.argsort(-ww,axis=1)[:,:4];mask=np.zeros_like(ww);np.put_along_axis(mask,keep,1,1);ww*=mask;ww/=ww.sum(1,keepdims=True)
names=[n+'_'+str(i) for i,n in enumerate(rig['names'])];keys=['hair','head','upper','left_arm','right_arm','lower'];manifest=[];materials={};arrays={};inspection=[];offset=0
for oi,o in enumerate(objects):
    old=o.name;p=positions[old];w=ww[offset:offset+len(p)];offset+=len(p);key=keys[oi]
    for v,co in zip(o.data.vertices,p):v.co=co
    o.matrix_world=Matrix.Identity(4);o.data.update();o.data.normals_split_custom_set(normaldata[old].tolist())
    for g in list(o.vertex_groups):o.vertex_groups.remove(g)
    for i,n in enumerate(names):
        g=o.vertex_groups.new(name=n)
        for vi in np.flatnonzero(w[:,i]>1e-7):g.add([int(vi)],float(w[vi,i]),'REPLACE')
    mat=o.data.materials[0];im=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    im.filepath_raw=str(R/'tex'/(key+'.png'));im.file_format='PNG';im.save();im.pack();mat.name='modern_girl_'+key
    materials[key]=dict(diffuse=key+'.png',normal=None,specular=None,cutout=False)
    o.name='modern_girl_part_'+str(oi).zfill(2);o.data.calc_loop_triangles()
    manifest.append(dict(object=o.name,source_object=old,part='body',material=key,kind='hair' if oi==0 else 'body'))
    arrays[o.name+'_p']=p;arrays[o.name+'_w']=w;arrays[o.name+'_f']=np.array([list(t.vertices) for t in o.data.loop_triangles],dtype='i4')
    inspection.append(dict(object=old,vertices=len(p),triangles=len(o.data.loop_triangles),bbox_m=[p.min(0).tolist(),p.max(0).tolist()]))
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name=cfg['skeleton'];bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0])
for i,n in enumerate(names):b=arm.data.edit_bones.new(n);b.matrix=Matrix(world[i].tolist());b.length=.04
for i,n in enumerate(names):
    if rig['parent'][i]>=0:arm.data.edit_bones[n].parent=arm.data.edit_bones[names[rig['parent'][i]]]
bpy.ops.object.mode_set(mode='OBJECT')
for o in objects:mod=o.modifiers.new('Race binding','ARMATURE');mod.object=arm;o.parent=arm
(R/'build/manifest.json').write_text(json.dumps(manifest,indent=2));np.savez_compressed(R/'build/fitted_model.npz',**arrays)
(R/'tex/materials.json').write_text(json.dumps(materials,indent=2));(R/'reports/input_inspection.json').write_text(json.dumps(inspection,indent=2))
(R/'reports/input_hashes.json').write_text(json.dumps({'input/model.fbx':hashlib.sha256((R/'input/model.fbx').read_bytes()).hexdigest()},indent=2))
(R/'reports/weight_transfer.json').write_text(json.dumps(dict(source_proportions_preserved=True,height_m=float(np.ptp(pts[:,2])),uniform_scale=scale,rotation=rot.tolist(),cloth_simulation=False,hand_pose='source fixed',landmarks_m=S.tolist()),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/ModernGirlRace_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/ModernGirlRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
print('SOURCE_READY',pts.min(0),pts.max(0))
