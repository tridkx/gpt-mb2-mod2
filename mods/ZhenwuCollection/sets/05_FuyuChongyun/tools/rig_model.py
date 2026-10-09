"""Fuyu-specific anatomical fit to current native bind matrices."""
import bpy, json, sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
cfg=json.loads((ROOT/'tools/model_config.json').read_text(encoding='utf-8'))
rigdata=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
world=rigdata['restWorld'];target=world[:,:3,3];parents=rigdata['parent'];N=len(target)
names=['bip01_'+n+'_'+str(i) for i,n in enumerate(rigdata['names'])]
source=np.zeros((N,3));lm=cfg['source_landmarks'];scale=cfg['source_coordinate_to_meters']
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
    d=np.array(dist).T;v=np.exp(np.maximum(-(d-d.min(1,keepdims=True))/.018,-30));v[v<.018]=0
    w=np.zeros((len(p),N));w[:,allowed]=v;return w/w.sum(1,keepdims=True)
def body_weights(p,arms=True):
    torso=weights(p,[0,9,10,11,12]);right=smooth(-.045,.045,p[:,0])
    leg=weights(p,[0,1,2,3,4])*(1-right[:,None])+weights(p,[0,5,6,7,8])*right[:,None]
    lower=1-smooth(.955,1.045,p[:,2]);w=torso*(1-lower[:,None])+leg*lower[:,None]
    if arms:
        for sign,allowed,elbow,hand in [(-1,[14,15,17,19],17,19),(1,[21,22,24,26],24,26)]:
            ids=np.where(p[:,0]*sign>=0)[0];q=p[ids];upper=15 if sign<0 else 22
            axis=source[elbow]-source[upper];t=(q-source[upper])@axis/(axis@axis)
            bend=smooth(.65,1.12,t);arm=np.zeros((len(q),N));arm[:,upper]=1-bend;arm[:,elbow]=bend
            axis=source[hand]-source[elbow];t=(q-source[elbow])@axis/(axis@axis)
            palm=smooth(.84,1.02,t);arm*=1-palm[:,None];arm[:,hand]+=palm
            blend=smooth(.105,.245,abs(q[:,0]));w[ids]=w[ids]*(1-blend[:,None])+arm*blend[:,None]
    # Face features begin at source z116; all lips/eyes must be rigid head.
    # Only the actual lower-neck ring blends with neck/spine.
    head=smooth(1.397,1.445,p[:,2])*(1-smooth(.07,.12,abs(p[:,0])))
    w*=1-head[:,None];w[:,13]+=head
    return normalize(w)
def rotation(a,b):
    aa=a/np.linalg.norm(a);bb=b/np.linalg.norm(b);v=np.cross(aa,bb);c=aa@bb
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+k+k@k/max(1+c,1e-8)
transforms=[]
for i in range(N):
    m=np.eye(3)
    if i in nxt and i not in [19,26]:
        a=source[nxt[i]]-source[i];b=target[nxt[i]]-target[i];aa=a/np.linalg.norm(a)
        m=rotation(a,b)@(np.eye(3)+(np.linalg.norm(b)/np.linalg.norm(a)-1)*np.outer(aa,aa))
    elif i in [19,26]:
        fore=17 if i==19 else 24;m=rotation(source[i]-source[fore],target[i]-target[fore])
    transforms.append(m)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'input/model.fbx'),use_anim=False)
objects=sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name)
assert {o.name for o in objects}==set(cfg['parts'])
arrays={};records=[];seams={};panel_plans={}
for oi,o in enumerate(objects):
    original=o.name;part,mat,kind=cfg['parts'][original]
    if original in cfg.get('uv_flip_v_objects',[]):
        for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
    # World source coordinates already face +Y. Do not copy Fuyu's rotation.
    p=np.round(np.array([o.matrix_world@v.co for v in o.data.vertices])*scale,5)
    w=body_weights(p,arms=kind not in ['legs','mixed_coat']);alpha=np.zeros(len(p))
    if kind in ['rigid_head','long_hair']:
        w[:]=0;w[:,13]=1
        if kind=='long_hair':alpha=cfg['cloth_max_distance'][kind]*(1-smooth(1.395,1.57,p[:,2]))
    if kind=='hands':
        # This mesh also has two tiny elbow-skin patches. Only the actual
        # palms/fingers beyond the wrist belong wholly to the hand bones.
        palm=abs(p[:,0])>.44
        w[palm]=0;w[palm & (p[:,0]<0),19]=1;w[palm & (p[:,0]>=0),26]=1
    if mat=='pants':
        # Rigid soles follow the foot, with a smooth ankle transition.
        sole=1-smooth(.12,.22,p[:,2]);feet=np.zeros_like(w)
        feet[p[:,0]<0,3]=1;feet[p[:,0]>=0,7]=1
        w=w*(1-sole[:,None])+feet*sole[:,None]
    if kind=='mixed_coat':
        waist=weights(p,[0,9]);right=smooth(-.16,.16,p[:,0]);low=1-smooth(.30,.65,p[:,2])
        legs=np.zeros_like(w);legs[:,1]=(1-right)*(1-low*.35);legs[:,2]=(1-right)*low*.35
        legs[:,5]=right*(1-low*.35);legs[:,6]=right*low*.35
        side=smooth(.045,.14,abs(p[:,0]))
        follow=(.55+.40*side)*(1-smooth(.85,1.00,p[:,2]))
        rear=smooth(.12,.24,-p[:,1]);follow*=1-rear*(1-cfg.get("skirt_rear_follow_scale",1))
        skirt=waist*(1-follow[:,None])+legs*follow[:,None]
        region=1-smooth(.92,1.055,p[:,2]);w=w*(1-region[:,None])+skirt*region[:,None]
        alpha=cfg['cloth_max_distance']['skirt']*(1-smooth(.30,1.01,p[:,2]))
    if kind=='upper_clothes':
        # Garment sleeves end at the elbows, no separate hanging cuff ribbons.
        # Keep actual arm projection; only lower free edges get small budgets.
        alpha=cfg['cloth_max_distance'][kind]*(1-smooth(1.10,1.34,p[:,2]))*smooth(.15,.26,abs(p[:,0]))
        # Skin and sleeve use the same continuous arm-axis projection.
        # Circumference offsets no longer select different nearest bones.
    # Independently measured hanging sleeve/cape components: upper roots
    # anchor to arms or torso; descending tips must not select leg bones.
    panels=[]
    if kind=='upper_clothes' or (kind=='mixed_coat' and cfg.get('pin_central_skirt_panels')):
        links=[[] for _ in p]
        for edge in o.data.edges:
            u,v=edge.vertices;links[u].append(v);links[v].append(u)
        visited=set();all_components=[]
        for start in range(len(p)):
            if start in visited:continue
            component=[];stack=[start];visited.add(start)
            while stack:
                v=stack.pop();component.append(v)
                for u in links[v]:
                    if u not in visited:visited.add(u);stack.append(u)
            ids=np.array(component,dtype=int);all_components.append(ids);q=p[ids];low=q[:,2].min();high=q[:,2].max()
            if kind=='mixed_coat' and abs(q[:,0]).max()>.065:continue
            if len(ids)<8 or high-low<.20 or high>1.40:continue
            roots=ids[p[ids,2]>high-.045]
            if not len(roots):continue
            anchor=p[roots].mean(0);arm=abs(anchor[0])>.12
            fixed=normalize(body_weights(p[roots],arms=arm).mean(0)[None])[0]
            if arm:
                # A fitted forearm segment can have a large vertical span.
                # Only cloth falling >20 cm below the measured arm axis is hanging.
                axis_z=np.interp(abs(q[:,0]),[.1875,.34375,.46875],[1.3375,1.175,1.0125])
                if np.max(axis_z-q[:,2])<.20:continue
            free=1-smooth(high-.17,high-.04,p[ids,2])
            w[ids]=w[ids]*(1-free[:,None])+fixed[None]*free[:,None]
            alpha[ids]=np.maximum(alpha[ids],cfg['hanging_panel_max_distance']*free)
            alpha[roots]=0
            panels.append({'ids':ids,'roots':roots,'free':free,'anchor':anchor,'weights':fixed,'attachment':'arm' if arm else 'torso'})
        if kind=='upper_clothes' and panels:
            # UV-split decorative tips inherit their adjacent hanging sheet attachment.
            # Their low position must not select calf/hand bones independently.
            main_panels=list(panels);claimed=set(int(i) for panel in panels for i in panel['ids'])
            for ids in all_components:
                if int(ids[0]) in claimed:continue
                q=p[ids]
                if q[:,2].max()>1.08:continue
                choices=[]
                for panel in main_panels:
                    if panel['anchor'][0]*q[:,0].mean()<0:continue
                    distance=np.linalg.norm(q[:,None,:]-p[panel['ids']][None,:,:],axis=2).min(axis=1)
                    choices.append((float(np.median(distance)),panel))
                if not choices:continue
                distance,panel=min(choices,key=lambda x:x[0])
                if distance>.10:continue
                high=p[panel['roots'],2].max()
                free=1-smooth(high-.17,high-.04,q[:,2])
                fixed=panel['weights'];w[ids]=w[ids]*(1-free[:,None])+fixed[None]*free[:,None]
                alpha[ids]=np.maximum(alpha[ids],cfg['hanging_panel_max_distance']*free)
                panels.append({'ids':ids,'roots':np.array([],dtype=int),'free':free,'anchor':panel['anchor'],'weights':fixed,'attachment':'adjacent_'+panel['attachment']})
    duplicate_groups={}
    for vi,co in enumerate(p):duplicate_groups.setdefault(tuple(co),[]).append(vi)
    if kind in ['upper_clothes','mixed_coat']:
        for ids in duplicate_groups.values():
            if len(ids)>1:
                w[ids]=normalize(w[ids].mean(0)[None])[0];alpha[ids]=alpha[ids].min()
    name='zw_fuyu_'+part+'_'+str(oi).zfill(2);o.name=name
    arrays[name]={'S':p,'W':normalize(w),'A':alpha};panel_plans[name]=panels
    records.append({'hanging_panels':[{'vertices':len(v['ids']),'root_vertices':v['roots'].tolist(),'anchor_source_m':v['anchor'].tolist(),'attachment':v['attachment']} for v in panels],'object':name,'source_object':original,'part':part,'kind':kind,'material':'zw_fuyu_'+mat,'texture_key':mat,'vertices':len(p)})
    # Align all skin cuts, including different equipment slots.
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
    b=rig.data.edit_bones.new(n);b.head=(0,0,0);b.tail=(0,.05,0);b.matrix=Matrix(world[i].tolist())
for i,n in enumerate(names):
    if parents[i]>=0:rig.data.edit_bones[n].parent=rig.data.edit_bones[names[parents[i]]]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for o,rec in zip(objects,records):
    a=arrays[o.name];p,w,alpha=a['S'],a['W'],a['A'];d=np.zeros_like(p)
    for i in range(N):d+=w[:,i,None]*((p-source[i])@transforms[i].T+target[i])
    for panel in panel_plans[o.name]:
        anchor=panel['anchor'];weights_at_root=panel['weights']
        fitted=sum(weights_at_root[i]*((anchor-source[i])@transforms[i].T+target[i]) for i in range(N))
        ids=panel['ids'];free=panel['free'];hanging=fitted+(p[ids]-anchor)
        d[ids]=d[ids]*(1-free[:,None])+hanging*free[:,None]
    if rec['texture_key']=='pants':
        # Preserve the measured flat source shoe sole. Mapping toe direction
        # independently otherwise pitches the front through the floor.
        blend=1-smooth(.12,.22,p[:,2])
        for sign,bone in [(-1,3),(1,7)]:
            ids=np.where(p[:,0]*sign>0)[0];q=p[ids]-source[bone]+target[bone]
            q[:,2]+=.001-q[p[ids,2]<.004,2].min()
            d[ids]=d[ids]*(1-blend[ids,None])+q*blend[ids,None]
    if rec['kind']=='mixed_coat':
        free=1-smooth(.80,1.02,p[:,2]);rad=d[:,:2].copy();rad[:,1]-=.01
        rad/=np.maximum(np.linalg.norm(rad,axis=1,keepdims=True),1e-6);d[:,:2]+=rad*(.018*free[:,None])
    if rec['kind'] in ['upper_clothes','mixed_coat']:
        coincident={}
        for vi,co in enumerate(p):coincident.setdefault(tuple(co),[]).append(vi)
        for ids in coincident.values():
            if len(ids)>1:d[ids]=d[ids].mean(0)
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
    for n in mat.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image:
            texture=ROOT/'tex'/cfg['textures'][rec['texture_key']][0];n.image.filepath=str(texture);n.image.reload();n.image.pack();assert n.image.packed_file
    if cfg['textures'][rec['texture_key']][1]=='cutout':
        tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
        test=mat.node_tree.nodes.new('ShaderNodeMath');test.operation='GREATER_THAN';test.inputs[1].default_value=cfg.get('material_overrides',{}).get(rec['texture_key'],{}).get('alphaTest',.20)
        mat.node_tree.links.new(tex.outputs['Alpha'],test.inputs[0])
        opacity=mat.node_tree.nodes.new('ShaderNodeMath');opacity.operation='MULTIPLY'
        mat.node_tree.links.new(tex.outputs['Alpha'],opacity.inputs[0]);mat.node_tree.links.new(test.outputs[0],opacity.inputs[1]);mat.node_tree.links.new(opacity.outputs[0],bs.inputs['Alpha'])
skin=[o for o,r in zip(objects,records) if r['texture_key'] in ['skin','face']];ns={}
for o in skin:
    o.data.calc_loop_triangles()
    for tri in o.data.loop_triangles:
        v=[o.data.vertices[i] for i in tri.vertices];n=(v[1].co-v[0].co).cross(v[2].co-v[0].co)
        for x in v:
            key=tuple(round(c,5) for c in x.co);ns.setdefault(key,Vector((0,0,0)));ns[key]+=n
for o in skin:o.data.normals_split_custom_set_from_vertices([ns[tuple(round(c,5) for c in v.co)].normalized() for v in o.data.vertices])
rig['runtime_skeleton']='human_skeleton';rig['native_guid']=rigdata['guid'];rig['native_rest_preserved']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/ZhenwuFuyu_Rigged.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/ZhenwuFuyu_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
(ROOT/'build/rig_manifest.json').write_text(json.dumps(records,indent=2))
np.savez_compressed(ROOT/'build/rig_arrays.npz',source=source,target=target,world=world,**{n+'_'+k:v for n,a in arrays.items() for k,v in a.items()})
(ROOT/'reports/rig_fit.json').write_text(json.dumps({'source_scale':scale,'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'bone_names':names,'shared_skin_boundaries':shared,'native_skeleton_guid':rigdata['guid'],'parts':records},indent=2))
print('RIG_READY',len(objects),'meshes',sum(r['vertices'] for r in records),'vertices',len(shared),'shared skin points')
