import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
"""Bind the complete source girl body without warping the source mesh."""
import bpy,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
raw=json.loads((R/'reports/human_skeleton.json').read_text());rig=parse_skeljson(raw)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
objects=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name)
parts=json.loads((R/'input/parts.json').read_text());assert {o.name for o in objects}=={p['name'] for p in parts}
positions={o.name:np.array([o.matrix_world@v.co for v in o.data.vertices])*.01 for o in objects}
allp=np.concatenate(list(positions.values()))
# Source A-pose landmarks in metres; separate config is model specific.
cfg=json.loads((R/'tools/model_config.json').read_text());S=np.array(cfg['landmarks_m'],float)
assert cfg['source_height_range_m'][0]<np.ptp(allp[:,2])<cfg['source_height_range_m'][1]
world=rig['restWorld'].copy();world[:,:3,3]=S
alignment=[]
if cfg.get('align_arm_bind_axes'):
    # Native arm translations follow each parent's local X axis. Moving joints
    # without aligning that axis introduced lateral offsets under idle rotations.
    # Transport the native frame by the shortest rotation, retaining its roll.
    for i,start,end in [(15,15,17),(16,15,17),(17,17,19),(18,17,19),
                        (22,22,24),(23,22,24),(24,24,26),(25,24,26)]:
        a=world[i,:3,0].copy();v=S[end]-S[start];v/=np.linalg.norm(v)
        cross=np.cross(a,v);c=float(a@v)
        assert c>-.99
        K=np.array([[0,-cross[2],cross[1]],[cross[2],0,-cross[0]],[-cross[1],cross[0],0]])
        Q=np.eye(3)+K+K@K/(1+c)
        world[i,:3,:3]=Q@world[i,:3,:3]
        alignment.append({'bone':rig['names'][i],'rotation_degrees':float(np.degrees(np.arccos(np.clip(c,-1,1))))})
(R/'reports/arm_bind_alignment.json').write_text(json.dumps({'enabled':bool(cfg.get('align_arm_bind_axes')),'bones':alignment,'joint_positions_unchanged':True},indent=2))
local=np.array([world[i] if p<0 else np.linalg.inv(world[p])@world[i] for i,p in enumerate(rig['parent'])])
bones=[]
for i,b in enumerate(raw['bones']):
    mat=np.array(b['rest']).reshape(4,4).T;mat[:3,:3]=local[i,:3,:3];mat[:3,3]=local[i,:3,3]
    bones.append({'name':b['name'],'parent':b['parent'],'rest':mat.T.reshape(-1).tolist()})
(R/'build/skeleton_spec.json').write_text(json.dumps(bones,indent=2))
nextbone={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,17:19,18:19,19:20,21:22,22:24,24:26,25:26,26:27}
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def near(p,ids):
    ds=[]
    for i in ids:
        a=S[i];b=S[nextbone[i]] if i in nextbone else a+(a-S[rig['parent'][i]])*.5
        # Item bones sit in the palm; keep the accepted hand skinning extent.
        if rig['names'][i] in cfg.get('hand_weight_tips_m',{}):
            b=np.array(cfg['hand_weight_tips_m'][rig['names'][i]])
        v=b-a;t=np.clip((p-a)@v/max(v@v,1e-10),0,1);ds.append(np.linalg.norm(p-a-t[:,None]*v,axis=1))
    ds=np.array(ds).T;v=np.exp(np.maximum(-(ds-ds.min(1,keepdims=True))/cfg['weight_softness_m'],-25));w=np.zeros((len(p),28));w[:,ids]=v;return w/w.sum(1,keepdims=True)
def body(p,arms=True):
    # Continuous two-joint torso interpolation leaves room for arm weights.
    # Dense distance weights followed by top-four truncation caused shoulder
    # discontinuities on the closely spaced source triangles.
    w=np.zeros((len(p),28));w[:,0]=1
    for lower,upper in [(0,9),(9,10),(10,11),(11,12)]:
        t=smooth(S[lower,2],S[upper,2],p[:,2])
        active=p[:,2]>=S[lower,2]
        w[active]=0;w[active,lower]=1-t[active];w[active,upper]=t[active]
    lo=1-smooth(.75,.87,p[:,2]);side=smooth(-.065,.065,p[:,0])
    legs=near(p,[0,1,2,3,4])*(1-side[:,None])+near(p,[0,5,6,7,8])*side[:,None]
    w=w*(1-lo[:,None])+legs*lo[:,None]
    if arms:
        for sign,ids in [(-1,[14,15,17,19]),(1,[21,22,24,26])]:
            ix=np.where(p[:,0]*sign>=0)[0];a=smooth(.07,.13,abs(p[ix,0]))*smooth(.10,.18,abs(p[ix,0])+.6*(p[ix,2]-.89));w[ix]=w[ix]*(1-a[:,None])+near(p[ix],ids)*a[:,None]
    h=smooth(1.12,1.155,p[:,2])*(1-smooth(.052,.09,abs(p[:,0])));w*=1-h[:,None];w[:,13]+=h
    return w
non_skirt_keys={tuple(np.round(v,5)) for name,p in positions.items() if name!=cfg['skirt_source'] for v in p}
manifest=[];materials={};weights={};arrays={};inspection=[]
for o in objects:
    p=positions[o.name];row=next(r for r in parts if r['name']==o.name);tex=row['tex']
    assert len(o.material_slots)==1 and o.data.uv_layers.active
    images=[n.image for n in o.material_slots[0].material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    assert any(tex in im.name or tex in im.filepath for im in images),(o.name,tex,[(im.name,im.filepath) for im in images])
    head=tex in ['hair_D','head_D','eye_D','eyelash_D','face_D'];w=body(p,arms=row['name'] not in cfg['legs_sources']+[cfg['skirt_source']])
    if tex.startswith('tunic_D') or row['name']==cfg.get('upper_skin_source'):
        # Hanging sleeve tips belong to their arm attachment, even when the
        # source A-pose puts them beside the thigh. Project the weight query
        # onto this model's measured arm line; leave garment vertices intact.
        proxy=p.copy();x=abs(p[:,0])
        for sign,shoulder,elbow,wrist in [(-1,15,17,19),(1,22,24,26)]:
            ix=np.where((p[:,0]*sign>abs(S[shoulder,0])+ .015))[0]
            knots=np.array([abs(S[i,0]) for i in [shoulder,elbow,wrist]])
            arm_z=np.interp(x[ix],knots,S[[shoulder,elbow,wrist],2])
            arm_y=np.interp(x[ix],knots,S[[shoulder,elbow,wrist],1])
            hang=smooth(.02,.08,arm_z-p[ix,2])
            proxy[ix,2]=p[ix,2]*(1-hang)+arm_z*hang
            proxy[ix,1]=p[ix,1]*(1-hang)+arm_y*hang
        w=body(proxy,arms=False)
        for sign,upper,fore,handbone in [(-1,15,17,19),(1,22,24,26)]:
            ix=np.where(p[:,0]*sign>=0)[0];x=abs(p[ix,0])
            elbow_x=abs(S[fore,0]);wrist_x=abs(S[handbone,0])
            lower=smooth(elbow_x-.09,elbow_x+.09,x)
            palm=smooth(wrist_x-.09,wrist_x+.09,x)
            arm=np.zeros((len(ix),28));arm[:,upper]=1-lower
            arm[:,fore]=lower*(1-palm);arm[:,handbone]=lower*palm
            amount=smooth(.07,.145,x)
            if row['name']==cfg['skirt_source']:amount*=smooth(.86,.98,p[ix,2])
            w[ix]=w[ix]*(1-amount[:,None])+arm*amount[:,None]
    if head:w[:]=0;w[:,13]=1
    # Connected hanging cloth follows its attachment rather than distant legs.
    parent=list(range(len(p)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for e in o.data.edges:a,b=e.vertices;parent[root(a)]=root(b)
    comps={}
    for i in range(len(p)):comps.setdefault(root(i),[]).append(i)
    for ids in comps.values():
        q=p[ids];low=q.min(0);high=q.max(0);mid=q.mean(0)
        if row['name']==cfg['skirt_source']:
            # Garment attachments follow this model's shorts/hip region.
            amount=1-smooth(.78,.88,q[:,2]);side=smooth(-.12,.12,q[:,0])
            reference=positions[cfg['legs_sources'][0]]
            reference_weights=weights[cfg['legs_sources'][0]]
            fitted=[]
            for sign in [-1,1]:
                band=(reference[:,0]*sign>.02)&(reference[:,2]>.70)&(reference[:,2]<.82)
                assert band.sum()>20
                fitted.append(reference_weights[band].mean(0))
            # Continuous across coincident flap/panel/ornament attachments.
            # Use this model's own protected surface binding; no knee/foot hem
            # influence. The fitted waist transitions to the original body skin.
            skirt=fitted[0][None,:]*(1-side[:,None])+fitted[1][None,:]*side[:,None]
            previous=np.zeros((len(ids),28));previous[:,0]=.90;previous[:,1]=.10*(1-side);previous[:,5]=.10*side
            boundary_reference=w[ids]*(1-amount[:,None])+previous*amount[:,None]
            revised=w[ids]*(1-amount[:,None])+skirt*amount[:,None]
            boundary=np.array([tuple(np.round(v,5)) in non_skirt_keys for v in q])
            revised[boundary]=boundary_reference[boundary]
            w[ids]=revised
        if tex=='cuff_D':w[ids]=near(q,[17,19] if mid[0]<0 else [24,26])
    weights[o.name]=w
    inspection.append({'object':o.name,'vertices':len(p),'bbox_m':[p.min(0).tolist(),p.max(0).tolist()],'diffuse':tex+'.png','cutout':row['alpha']})
# Shared points receive identical weights across neck, shoulder and wrist seams.
pts=np.concatenate(list(positions.values()));ww=np.concatenate(list(weights.values()));unique,owner=np.unique(np.round(pts,5),axis=0,return_inverse=True)
avg=np.zeros((len(unique),28));np.add.at(avg,owner,ww);avg/=np.bincount(owner)[:,None];ww=avg[owner]
keep=np.argsort(-ww,axis=1)[:,:4];mask=np.zeros_like(ww);np.put_along_axis(mask,keep,1,1);ww*=mask;ww/=ww.sum(1,keepdims=True)
offset=0;names=[n+'_'+str(i) for i,n in enumerate(rig['names'])]
for oi,o in enumerate(objects):
    old=o.name;p=positions[old];w=ww[offset:offset+len(p)];offset+=len(p);row=next(r for r in inspection if r['object']==old);tex=row['diffuse'][:-4]
    for v,co in zip(o.data.vertices,p):v.co=co
    o.matrix_world=Matrix.Identity(4)
    for g in list(o.vertex_groups):o.vertex_groups.remove(g)
    for i,n in enumerate(names):
        g=o.vertex_groups.new(name=n)
        for vi in np.flatnonzero(w[:,i]>1e-7):g.add([int(vi)],float(w[vi,i]),'REPLACE')
    o.name='txgirl6_part_'+str(oi).zfill(2);o.data.calc_loop_triangles()
    manifest.append({'object':o.name,'source_object':old,'part':'body','material':tex,'kind':'hair' if tex in ['hair_D','head_D','eyelash_D'] else 'body'})
    arrays[o.name+'_p']=p;arrays[o.name+'_w']=w
    arrays[o.name+'_f']=np.array([list(t.vertices) for t in o.data.loop_triangles],dtype='i4')
    materials[tex]={'diffuse':tex+'.png','normal':None,'specular':None,'cutout':row['cutout']}
    mat=o.material_slots[0].material;mat.name='txgirl6_'+tex.lower()
    for im in [n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]:im.filepath=str(R/'tex'/(tex+'.png'));im.reload();im.pack()
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name=cfg['skeleton'];bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0])
for i,n in enumerate(names):b=arm.data.edit_bones.new(n);b.matrix=Matrix(world[i].tolist());b.length=.04
for i,n in enumerate(names):
    if rig['parent'][i]>=0:arm.data.edit_bones[n].parent=arm.data.edit_bones[names[rig['parent'][i]]]
bpy.ops.object.mode_set(mode='OBJECT')
for o in objects:mod=o.modifiers.new('Race binding','ARMATURE');mod.object=arm;o.parent=arm
(R/'build/manifest.json').write_text(json.dumps(manifest,indent=2));np.savez_compressed(R/'build/fitted_model.npz',**arrays)
(R/'tex/materials.json').write_text(json.dumps(materials,indent=2))
(R/'reports/input_inspection.json').write_text(json.dumps(inspection,indent=2))
(R/'reports/input_hashes.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'input').rglob('*') if p.is_file()},indent=2))
(R/'reports/weight_transfer.json').write_text(json.dumps({'source_geometry_max_error_m':0,'source_proportions_preserved':True,'height_m':float(np.ptp(allp[:,2])),'landmarks_m':S.tolist(),'unit_scale':.01,'orientation':[1,1,1]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/TianxiangGirlT6Race_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/TianxiangGirlT6Race_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
print('SOURCE_READY',len(manifest),allp.min(0),allp.max(0))
