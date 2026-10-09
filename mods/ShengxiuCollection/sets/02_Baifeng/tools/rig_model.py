"""Baifeng original meshes, measured source landmarks and native human binding."""
import bpy, json, sys, re, heapq
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))

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
    lower=1-smooth(.99,1.17,p[:,2]);w=torso*(1-lower[:,None])+leg*lower[:,None]
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
    head=smooth(1.53,1.58,p[:,2])*(1-smooth(.07,.12,np.abs(p[:,0])))
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
arrays={};records=[];seams={};veil_panels={};veil_report=[]
arm_skin=np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices])*cfg['input_scale']@np.array(cfg['input_axis']).T for o in objects if cfg['parts'][o.name][1]=='skin' and cfg['parts'][o.name][2]=='arms'])
arm_skin_weights=body_weights(arm_skin)
for o in objects:
    original=o.name;part,mat,kind=cfg['parts'][original]
    if original in cfg.get('uv_flip_v_objects',[]):
        for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
    p=np.round(np.array([o.matrix_world@v.co for v in o.data.vertices])*cfg['input_scale']@np.array(cfg['input_axis']).T,5)
    w=body_weights(p,arms=kind not in ['legs','skirt','torso']);alpha=np.zeros(len(p))
    if kind=='arm_ornament':
        w[:]=0;w[p[:,0]<0,15]=1;w[p[:,0]>=0,22]=1
    if kind in ['rigid_head','long_hair']:
        w[:]=0;w[:,13]=1
        if kind=='long_hair':alpha=cfg['cloth_max_distance'][kind]*(1-smooth(1.26,1.66,p[:,2]))
    if kind=='skirt':
        waist=weights(p,[0,9]);right=smooth(-.20,.20,p[:,0]);low=1-smooth(.35,.72,p[:,2])
        legs=np.zeros_like(w)
        legs[:,1]=(1-right)*(1-low*.15);legs[:,2]=(1-right)*low*.15
        legs[:,5]=right*(1-low*.15);legs[:,6]=right*low*.15
        follow=cfg['skirt_thigh_follow']*(1-smooth(.92,1.24,p[:,2]));w=waist*(1-follow[:,None])+legs*follow[:,None]
        alpha=cfg['cloth_max_distance'][kind]*(1-smooth(.40,1.24,p[:,2]))
    if kind=='hanging_clothes':
        topology=list(range(len(p)))
        def topfind(v):
            while topology[v]!=v:topology[v]=topology[topology[v]];v=topology[v]
            return v
        bypos={}
        for vi,co in enumerate(p):
            if tuple(co) in bypos:topology[topfind(vi)]=topfind(bypos[tuple(co)])
            else:bypos[tuple(co)]=vi
        for edge in o.data.edges:topology[topfind(edge.vertices[1])]=topfind(edge.vertices[0])
        pieces={}
        for vi in range(len(p)):pieces.setdefault(topfind(vi),[]).append(vi)
        hip=np.zeros(len(p),bool)
        for ids in pieces.values():
            if p[ids,2].max()<source[0,2]+.15:hip[ids]=True
        w[hip]=0;w[hip,0]=1
        for sign,upper,anchor,hand in [(-1,15,17,19),(1,22,24,26)]:
            ids=np.flatnonzero((p[:,0]*sign>.14)&~hip)
            if not len(ids):continue
            q=p[ids];x=abs(q[:,0]);xu=abs(source[upper,0]);xe=abs(source[anchor,0]);xh=abs(source[hand,0])
            t=np.clip((x-xu)/(xe-xu),0,1);f=np.clip((x-xe)/(xh-xe),0,1)
            arm=np.zeros((len(ids),28));arm[:,upper]=1-t;arm[:,anchor]=t*(1-f);arm[:,hand]=f
            blend=smooth(.14,.22,x)
            w[ids]=w[ids]*(1-blend[:,None])+arm*blend[:,None]
            # Close cloth/armor around an exposed arm uses the exact skin
            # neighbourhood, avoiding mismatched forearm and hand rotation.
            distance=np.linalg.norm(q[:,None,:]-arm_skin[None,:,:],axis=2)
            nearest=np.argsort(distance,axis=1)[:,:4]
            local=np.take_along_axis(distance,nearest,axis=1)
            influence=1/np.maximum(local,.002)**3;influence/=influence.sum(1,keepdims=True)
            skinw=(arm_skin_weights[nearest]*influence[:,:,None]).sum(1)
            contact=1-smooth(.025,.060,local[:,0])
            w[ids]=w[ids]*(1-contact[:,None])+skinw*contact[:,None]
            veil_panels.setdefault(o.name,[]).append((ids,anchor))
    if kind in cfg['cloth_max_distance']:
        # Connected-component root painting avoids accidental free-floating
        # islands in hair cards, skirt layers and separate ribbons.
        parent=list(range(len(p)))
        def find(v):
            while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
            return v
        graph=[[] for _ in p];bypos={}
        for vi,co in enumerate(p):
            key=tuple(co)
            if key in bypos:
                u=bypos[key];parent[find(vi)]=find(u)
                graph[vi].append((u,0));graph[u].append((vi,0))
            else:bypos[key]=vi
        for edge in o.data.edges:
            u,v=map(int,edge.vertices);parent[find(v)]=find(u)
            length=float(np.linalg.norm(p[u]-p[v]));graph[u].append((v,length));graph[v].append((u,length))
        panels={}
        for vi in range(len(p)):panels.setdefault(find(vi),[]).append(vi)
        alpha[:]=0
        for ids in panels.values():
            q=p[ids]
            if len(ids)<12 or np.ptp(q[:,2])<.06:continue
            if kind=='hanging_clothes' and not any(set(ids)==set(v[0]) for v in veil_panels.get(o.name,[])):continue
            roots=[i for i in ids if p[i,2]>=q[:,2].max()-.015]
            distance={i:float('inf') for i in ids};queue=[]
            for i in roots:distance[i]=0;heapq.heappush(queue,(0,i))
            while queue:
                value,u=heapq.heappop(queue)
                if value!=distance[u]:continue
                for v,length in graph[u]:
                    trial=value+length
                    if trial<distance[v]:distance[v]=trial;heapq.heappush(queue,(trial,v))
            travel=np.array([distance[i] for i in ids]);assert np.isfinite(travel).all()
            budget=cfg['cloth_max_distance'][kind]
            alpha[ids]=np.minimum(travel*.8,budget)
            veil_report.append({'source_object':o.name,'kind':kind,'fixed_vertices':roots,'max_path_m':float(travel.max())})
    if kind=='hanging_clothes':
        alpha[:]=0
        for ids,anchor in veil_panels.get(o.name,[]):
            axis=normalize(w[ids].copy())@source
            below=axis[:,2]-p[ids,2]
            alpha[ids]=np.minimum(np.maximum(below-.04,0)*.8,cfg['cloth_max_distance'][kind])
    name='sx_baifeng_'+part+'_'+str(objects.index(o)).zfill(2);o.name=name
    arrays[name]={'S':p,'W':normalize(w),'A':alpha,'veils':veil_panels.get(original,[])}
    records.append({'object':name,'source_object':original,'part':part,'kind':kind,'material':'sx_baifeng_'+mat,'texture_key':mat,'vertices':len(p)})
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
    for ids,anchor in a['veils']:
        if anchor==0:continue
        q=p[ids];localw=w[ids]
        source_axis=localw@source;target_axis=localw@target
        relative=q-source_axis
        hanging=target_axis+relative
        free=smooth(.04,.12,source_axis[:,2]-q[:,2])
        d[ids]=d[ids]*(1-free[:,None])+hanging*free[:,None]
    if rec['kind']=='skirt':
        free=1-smooth(.85,1.10,p[:,2]);rad=d[:,:2].copy();rad[:,1]-=.01
        rad/=np.maximum(np.linalg.norm(rad,axis=1,keepdims=True),1e-6);d[:,:2]+=rad*(.009*free[:,None])
    if rec['kind']=='long_hair':d[:,1]-=.006*(1-smooth(1.26,1.66,p[:,2]))
    if rec['part']=='legs':
        settings=cfg['foot_fit'];pivot=np.array(settings['pivot']);theta=np.deg2rad(settings['pitch_degrees'])
        rot=np.array([[1,0,0],[0,np.cos(theta),-np.sin(theta)],[0,np.sin(theta),np.cos(theta)]])
        corrected=(d-pivot)@rot.T+pivot
        corrected[:,1]=pivot[1]+(corrected[:,1]-pivot[1])*settings['length_scale']
        corrected[:,2]+=settings['ground_shift_m']
        influence=1-smooth(.13,.27,d[:,2]);d+=influence[:,None]*(corrected-d)
    # Keep the accepted rest fit; move the animation pivot towards this model's
    # skull base by distributing head rotation between neck and head bones.
    a['fitW']=w.copy()
    follow=cfg['runtime_head_neck_follow']
    head_weight=w[:,13].copy();w[:,12]+=head_weight*follow;w[:,13]-=head_weight*follow
    if rec['texture_key'] in ['skin','face']:
        # The chin is at source z~1.549, but the old gradient extended to
        # 1.580 and pulled the lower jaw with spine2. Keep the entire jaw
        # on the same head transform; confine the blend to the neck ring.
        head=smooth(1.532,1.548,p[:,2])*(1-smooth(.10,.14,np.abs(p[:,0])))
        base=w.copy();base[:,13]=0
        base/=np.maximum(base.sum(1,keepdims=True),1e-12)
        w=base*(1-head[:,None]);w[:,12]+=head*follow;w[:,13]+=head*(1-follow)
    w=normalize(w);a['W']=w
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
    mat=bpy.data.materials.new(rec['material']+'_preview');mat.use_nodes=True
    o.data.materials.clear();o.data.materials.append(mat)
    for f in o.data.polygons:f.material_index=0
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Roughness'].default_value=.68
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(ROOT/'tex'/cfg['textures'][rec['texture_key']][0]),check_existing=False)
    tex.image.pack();mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if cfg['textures'][rec['texture_key']][1]!='opaque':
        test=mat.node_tree.nodes.new('ShaderNodeMath');test.operation='GREATER_THAN'
        test.inputs[1].default_value=cfg.get('material_overrides',{}).get(rec['texture_key'],{}).get('alphaTest',.2)
        mat.node_tree.links.new(tex.outputs['Alpha'],test.inputs[0]);mat.node_tree.links.new(test.outputs[0],bs.inputs['Alpha'])
# Share skin shading across UV and equipment cuts, using area-weighted normals.
skin=[o for o,r in zip(objects,records) if r['texture_key'] in ['skin','face']];ns={}
for o in skin:
    o.data.calc_loop_triangles()
    for tri in o.data.loop_triangles:
        v=[o.data.vertices[i] for i in tri.vertices];n=(v[1].co-v[0].co).cross(v[2].co-v[0].co)
        for x in v:ns.setdefault(tuple(round(c,5) for c in x.co),Vector((0,0,0)));ns[tuple(round(c,5) for c in x.co)]+=n
for o in skin:o.data.normals_split_custom_set_from_vertices([ns[tuple(round(c,5) for c in v.co)].normalized() for v in o.data.vertices])
rig['runtime_skeleton']='human_skeleton';rig['native_guid']=rigdata['guid'];rig['native_rest_preserved']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/sx_baifeng_Rigged.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/sx_baifeng_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
(ROOT/'build/rig_manifest.json').write_text(json.dumps(records,indent=2))
np.savez_compressed(ROOT/'build/rig_arrays.npz',source=source,target=target,world=world,**{n+'_'+k:v for n,a in arrays.items() for k,v in a.items() if k!='veils'})
(ROOT/'reports/rig_fit.json').write_text(json.dumps({'source_scale':scale,'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'bone_names':names,'shared_skin_boundaries':shared,'native_skeleton_guid':rigdata['guid'],'parts':records},indent=2))
(ROOT/'reports/veil_distance_plan.json').write_text(json.dumps({'panels':veil_report,'settings':cfg['cloth_max_distance'],'scope':'painted travel budgets; UnknownFloat1 scale equivalence remains inferred, game solver not run'},indent=2))
print('RIG_READY',len(objects),'meshes',sum(r['vertices'] for r in records),'vertices',len(shared),'shared skin points')
