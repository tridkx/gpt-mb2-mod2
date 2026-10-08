"""TianxiangFangzi original meshes, measured source landmarks and native human binding."""
import bpy, json, sys, re
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
raw=json.loads((ROOT/'reports/human_skeleton.json').read_text())
rigdata=parse_skeljson(raw);world=rigdata['restWorld'];target=world[:,:3,3];parents=rigdata['parent']
names=[(n if n.startswith('bip01_') else 'bip01_'+n)+'_'+str(i) for i,n in enumerate(rigdata['names'])]
assert len(names)==28
source=np.zeros((28,3));lm=cfg['source_landmarks'];scale=cfg['source_coordinate_to_meters']
for i,n in enumerate(rigdata['names']):
    if n in lm:source[i]=np.array(lm[n])*scale
    elif n[2:] in lm:
        source[i]=np.array(lm[n[2:]])*scale;source[i,0]*=-1 if n.startswith('l_') else 1
for twist,upper,elbow,fore,hand in [(16,15,17,18,19),(23,22,24,25,26)]:
    source[twist]=(source[upper]+source[elbow])/2;source[fore]=(source[elbow]+source[hand])/2
nxt={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,16:17,17:19,18:19,19:20,21:22,22:24,23:24,24:26,25:26,26:27}
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def normalize(w):
    keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask
    assert (w.sum(1)>0).all();return w/w.sum(1,keepdims=True)
def weights(p,allowed):
    dist=[]
    for i in allowed:
        a=source[i];b=source[nxt[i]] if i in nxt else a+(a-source[parents[i]])*.5
        axis=b-a;t=np.clip((p-a)@axis/max(axis@axis,1e-12),0,1)
        dist.append(np.linalg.norm(p-a-t[:,None]*axis,axis=1))
    d=np.array(dist).T;v=np.exp(np.maximum(-(d-d.min(1,keepdims=True))/.022,-30));v[v<.018]=0
    w=np.zeros((len(p),28));w[:,allowed]=v;return w/w.sum(1,keepdims=True)
def body_weights(p,arms=True):
    torso=weights(p,[0,9,10,11,12]);right=smooth(-.045,.045,p[:,0])
    leg=weights(p,[0,1,2,3,4])*(1-right[:,None])+weights(p,[0,5,6,7,8])*right[:,None]
    lower=1-smooth(.94,1.08,p[:,2]);w=torso*(1-lower[:,None])+leg*lower[:,None]
    if arms:
        for sign,allowed,fore,hand in [(-1,[14,15,17,19],17,19),(1,[21,22,24,26],24,26)]:
            ids=np.where(p[:,0]*sign>=0)[0];q=p[ids];arm=weights(q,allowed)
            axis=source[hand]-source[fore];t=(q-source[fore])@axis/(axis@axis)
            palm=smooth(.88,1.02,t)
            arm*=1-palm[:,None];arm[:,hand]+=palm
            # Hands lie at waist height in this A pose, but must never inherit
            # pelvis/thigh influences simply because their height is low.
            blend=smooth(.10,.23,np.abs(q[:,0]))
            w[ids]=w[ids]*(1-blend[:,None])+arm*blend[:,None]
    head=smooth(1.445,1.50,p[:,2])*(1-smooth(.07,.12,np.abs(p[:,0])))
    w*=1-head[:,None];w[:,13]+=head
    return normalize(w)
def rotation(a,b):
    aa=a/np.linalg.norm(a);bb=b/np.linalg.norm(b);v=np.cross(aa,bb);c=aa@bb
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+k+k@k/max(1+c,1e-8)
transforms=[]
for i in range(28):
    m=np.eye(3)
    if i in nxt and i not in [19,26]:
        a=source[nxt[i]]-source[i];b=target[nxt[i]]-target[i]
        aa=a/np.linalg.norm(a);m=rotation(a,b)@(np.eye(3)+(np.linalg.norm(b)/np.linalg.norm(a)-1)*np.outer(aa,aa))
    elif i in [19,26]:
        fore=17 if i==19 else 24
        m=rotation(source[i]-source[fore],target[i]-target[fore])
    transforms.append(m)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'input/model.fbx'),use_anim=False)
objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
assert {o.name for o in objects}==set(cfg['parts'])
arrays={};records=[];seams={}
for o in objects:
    original=o.name;part,mat,kind=cfg['parts'][original]
    if original in cfg.get('uv_flip_v_objects',[]):
        for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
    p=np.round(np.array([o.matrix_world@v.co for v in o.data.vertices])*scale,5)
    w=body_weights(p,arms=kind not in ['legs','skirt']);alpha=np.zeros(len(p))
    if kind in ['rigid_head','long_hair']:
        w[:]=0;w[:,13]=1
        if kind=='long_hair':alpha=cfg['cloth_max_distance'][kind]*(1-smooth(1.20,1.48,p[:,2]))
    if kind=='skirt':
        # Central tunic must not inherit the nearby forearm/hand at waist height.
        anatomical=body_weights(p,arms=False)
        parent=list(range(len(p)))
        def find(v):
            while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
            return v
        for edge in o.data.edges:parent[find(edge.vertices[1])]=find(edge.vertices[0])
        components={}
        for vi in range(len(p)):components.setdefault(find(vi),[]).append(vi)
        skirt_mask=np.zeros(len(p),bool)
        for ids in components.values():
            q=p[ids]
            if q[:,2].max()<cfg['mixed_skirt_component_max_z'] and q[:,2].mean()<cfg['mixed_skirt_component_mean_z']:skirt_mask[ids]=True
        width=cfg['skirt_center_width'];right=smooth(-width,width,p[:,0]);low=1-smooth(.40,.78,p[:,2]);amount=cfg['skirt_calf_share']
        left_calf=low*amount*(1-smooth(-width,0,p[:,0]));right_calf=low*amount*smooth(0,width,p[:,0])
        legs=np.zeros_like(w);legs[:,1]=(1-right)*(1-left_calf);legs[:,2]=(1-right)*left_calf;legs[:,5]=right*(1-right_calf);legs[:,6]=right*right_calf
        follow=cfg['skirt_thigh_follow']*(1-smooth(.87,1.09,p[:,2]));skirtw=legs*follow[:,None];skirtw[:,0]+=1-follow
        w=anatomical;w[skirt_mask]=skirtw[skirt_mask]
        alpha[skirt_mask]=cfg['cloth_max_distance'][kind]*(1-smooth(.43,1.10,p[skirt_mask,2]))
    if kind=='upper_clothes':
        if cfg.get('sleeve_projected_anchor'):
            parent=list(range(len(p)))
            def find(v):
                while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
                return v
            for e in o.data.edges:parent[find(e.vertices[1])]=find(e.vertices[0])
            panels={}
            for vi in range(len(p)):panels.setdefault(find(vi),[]).append(vi)
            for ids in panels.values():
                q=p[ids]
                if np.min(abs(q[:,0]))<=cfg.get('sleeve_panel_min_x',.10) or np.min(q[:,0])*np.max(q[:,0])<0:continue
                upper,elbow=(15,17) if q[:,0].mean()<0 else (22,24)
                t=cfg.get('sleeve_forearm_follow',.25)*smooth(abs(source[upper,0]),abs(source[elbow,0]),abs(q[:,0]))
                w[ids]=0;w[ids,upper]=1-t;w[ids,elbow]=t
        # Limit sleeve motion; attached torso, collar and waist remain pinned.
        for sign,upper,elbow in [(-1,15,17),(1,22,24)]:
            ids=np.where(p[:,0]*sign>.20)[0];q=p[ids];a=source[upper];axis=source[elbow]-a
            t=np.clip((q-a)@axis/(axis@axis),0,1);below=(a+t[:,None]*axis)[:,2]-q[:,2]
            alpha[ids]=cfg['cloth_max_distance'][kind]*smooth(.025,.11,below)
    name='fz5_'+part+'_'+original.split('_')[1];o.name=name
    arrays[name]={'S':p,'W':normalize(w),'A':alpha}
    records.append({'object':name,'source_object':original,'part':part,'kind':kind,'material':'fz5_'+mat,'texture_key':mat,'vertices':len(p)})
    if mat in ['skin','face']:
        for vi,co in enumerate(p):seams.setdefault(tuple(co),[]).append((name,vi))
shared=[]
for refs in seams.values():
    if len({n for n,i in refs})<2:continue
    w=normalize(np.mean([arrays[n]['W'][i] for n,i in refs],axis=0)[None])[0]
    for n,i in refs:arrays[n]['W'][i]=w;arrays[n]['A'][i]=0
    shared.append(refs)
bpy.ops.object.armature_add();rig=bpy.context.object;rig.name='human_skeleton_notused'
bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones.remove(rig.data.edit_bones[0])
for i,n in enumerate(names):
    b=rig.data.edit_bones.new(n)
    # A new edit bone has zero length. Give it a direction before assigning
    # the native matrix, otherwise Blender retains a default axis on import.
    b.head=(0,0,0);b.tail=(0,.05,0);b.matrix=Matrix(world[i].tolist())
for i,n in enumerate(names):
    if parents[i]>=0:rig.data.edit_bones[n].parent=rig.data.edit_bones[names[parents[i]]]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for o,rec in zip(objects,records):
    a=arrays[o.name];p,w,alpha=a['S'],a['W'],a['A'];d=np.zeros_like(p)
    for i in range(28):d+=w[:,i,None]*((p-source[i])@transforms[i].T+target[i])
    if rec['kind']=='skirt':
        free=(1-smooth(.85,1.10,p[:,2]))*(a['A']>0);rad=d[:,:2].copy();rad[:,1]-=.01
        rad/=np.maximum(np.linalg.norm(rad,axis=1,keepdims=True),1e-6);d[:,:2]+=rad*(.009*free[:,None])
    if rec['kind']=='long_hair':d[:,1]-=.006*(1-smooth(1.20,1.48,p[:,2]))
    a['P']=d;o.matrix_world=Matrix.Identity(4)
    for v,co in zip(o.data.vertices,d):v.co=co
    for f in o.data.polygons:f.use_smooth=True
    for i,n in enumerate(names):
        g=o.vertex_groups.new(name=n)
        for vi in np.where(w[:,i]>1e-6)[0]:g.add([int(vi)],float(w[vi,i]),'REPLACE')
    mod=o.modifiers.new('Native human skin','ARMATURE');mod.object=rig;o.parent=rig
    attr=o.data.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
    colors=np.ones((len(p),4));colors[:,3]=alpha;attr.data.foreach_set('color',colors.ravel());o.data.color_attributes.active_color=attr
    rec.update(cloth=bool(alpha.max()>.001),max_distance=float(alpha.max()),bounds=[d.min(0).tolist(),d.max(0).tolist()])
    mat=o.data.materials[0];mat.name=rec['material']+'_preview_'+o.name
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.68;bs.inputs['Metallic'].default_value=0
    if rec['texture_key']=='lash':
        tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
        test=mat.node_tree.nodes.new('ShaderNodeMath');test.operation='GREATER_THAN';test.inputs[1].default_value=cfg['material_overrides']['lash']['alphaTest']
        mat.node_tree.links.new(tex.outputs['Alpha'],test.inputs[0]);mat.node_tree.links.new(test.outputs[0],bs.inputs['Alpha'])
    for n in mat.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image:
            texture=ROOT/'tex'/cfg['textures'][rec['texture_key']][0];n.image.filepath=str(texture);n.image.reload();n.image.pack()
            assert n.image.packed_file
# Share skin shading across UV and equipment cuts, using area-weighted normals.
skin=[o for o,r in zip(objects,records) if r['texture_key'] in ['skin','face']];ns={}
for o in skin:
    o.data.calc_loop_triangles()
    for tri in o.data.loop_triangles:
        v=[o.data.vertices[i] for i in tri.vertices];n=(v[1].co-v[0].co).cross(v[2].co-v[0].co)
        for x in v:ns.setdefault(tuple(round(c,5) for c in x.co),Vector((0,0,0)));ns[tuple(round(c,5) for c in x.co)]+=n
for o in skin:o.data.normals_split_custom_set_from_vertices([ns[tuple(round(c,5) for c in v.co)].normalized() for v in o.data.vertices])
rig['runtime_skeleton']='human_skeleton';rig['native_guid']=rigdata['guid'];rig['native_rest_preserved']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/TianxiangFangzi_Rigged.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/TianxiangFangzi_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
(ROOT/'build/rig_manifest.json').write_text(json.dumps(records,indent=2))
np.savez_compressed(ROOT/'build/rig_arrays.npz',source=source,target=target,world=world,**{n+'_'+k:v for n,a in arrays.items() for k,v in a.items()})
(ROOT/'reports/rig_fit.json').write_text(json.dumps({'source_scale':scale,'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'bone_names':names,'shared_skin_boundaries':shared,'native_skeleton_guid':rigdata['guid'],'parts':records},indent=2))
print('RIG_READY',len(objects),'meshes',sum(r['vertices'] for r in records),'vertices',len(shared),'shared skin points')
