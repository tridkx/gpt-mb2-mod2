"""HanfuBlueRed-specific landmarks, parts, seam matching and native skeleton fit."""
import bpy, json, sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'build').mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'))
from repair_hair_contacts import repair
from level_shoes import level
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
rigdata=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
assert rigdata['boneCount']==28
world=rigdata['restWorld'];target=world[:,:3,3];parent=rigdata['parent']
names=[n+'_'+str(i) for i,n in enumerate(rigdata['names'])]
# Tripo normalized the original height to 1; +X is forward and +Y is left.
SCALE=1.70
def convert(p):
    p=np.asarray(p);return np.stack([-p[...,1],p[...,0],p[...,2]],axis=-1)*SCALE
anatomy={b['name']:np.array(b['head'])/.978515923 for b in json.loads((ROOT/'reports/source_skeleton.json').read_text())}
source=np.zeros((28,3))
for i,n in {0:'Hip',1:'L_Thigh',2:'L_Calf',5:'R_Thigh',6:'R_Calf',9:'Spine01',10:'Spine02',14:'L_Clavicle',15:'L_Upperarm',17:'L_Forearm',19:'L_Hand',21:'R_Clavicle',22:'R_Upperarm',24:'R_Forearm',26:'R_Hand'}.items():source[i]=convert(anatomy[n])
# Source AI foot/head pivots are not anatomical ankle/skull pivots; use visible bounds.
source[11]=convert([-.014,0,.72]);source[12]=convert([-.018,0,.804]);source[13]=convert([-.02,0,.852])
for side,ids in [('L',[3,4,16,18,20]),('R',[7,8,23,25,27])]:
    foot=anatomy[side+'_Foot'].copy();foot[2]=.04
    source[ids[0]]=convert(foot)
    toe=foot.copy();toe[0]=.057;toe[2]=.015;source[ids[1]]=convert(toe)
    upper,elbow,hand=(15,17,19) if side=='L' else (22,24,26)
    source[ids[2]]=(source[upper]+source[elbow])/2
    source[ids[3]]=(source[elbow]+source[hand])/2
    source[ids[4]]=convert(np.array(next(b['tail'] for b in json.loads((ROOT/'reports/source_skeleton.json').read_text()) if b['name']==side+'_Hand'))/.978515923)
nxt={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,16:17,17:19,18:19,19:20,21:22,22:24,23:24,24:26,25:26,26:27}
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def weights(p,allowed):
    ds=[]
    for i in allowed:
        a=source[i];b=source[nxt[i]] if i in nxt else a+(a-source[parent[i]])*.5
        axis=b-a;t=np.clip((p-a)@axis/max(axis@axis,1e-12),0,1)
        ds.append(np.linalg.norm(p-a-t[:,None]*axis,axis=1))
    d=np.array(ds).T;v=np.exp(np.maximum(-(d-d.min(1,keepdims=True))/.035,-30));v[v<.02]=0
    w=np.zeros((len(p),28));w[:,allowed]=v;return w/w.sum(1,keepdims=True)
def normalize(w):
    keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask
    return w/w.sum(1,keepdims=True)
def body_weights(p,use_arms=True):
    w=weights(p,[0,9,10,11,12])
    lower=1-smooth(.43*SCALE,.57*SCALE,p[:,2])
    right=smooth(-.045*SCALE,.045*SCALE,p[:,0])
    legs=weights(p,[0,1,2,3])*(1-right[:,None])+weights(p,[0,5,6,7])*right[:,None]
    w=w*(1-lower[:,None])+legs*lower[:,None]
    for sign,arm,leg in [(-1,[14,15,17,19],[0,1,2,3]),(1,[21,22,24,26],[0,5,6,7])]:
        ids=np.where(p[:,0]*sign>=0)[0];q=p[ids]
        base=w[ids]
        ab=smooth(.06*SCALE,.115*SCALE,np.abs(q[:,0]))*smooth(.65*SCALE,.735*SCALE,q[:,2]) if use_arms else np.zeros(len(q))
        w[ids]=base*(1-ab[:,None])+weights(q,arm)*ab[:,None]
    h=smooth(.795*SCALE,.848*SCALE,p[:,2])*(1-smooth(.06*SCALE,.105*SCALE,np.abs(p[:,0])))
    w*=1-h[:,None];w[:,13]+=h
    return normalize(w)
def affine(i):
    if i not in nxt:return np.eye(3)
    a=source[nxt[i]]-source[i];b=target[nxt[i]]-target[i];aa=a/np.linalg.norm(a);bb=b/np.linalg.norm(b)
    v=np.cross(aa,bb);c=aa@bb;k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return (np.eye(3)+k+k@k/max(1+c,1e-8))@(np.eye(3)+(np.linalg.norm(b)/np.linalg.norm(a)-1)*np.outer(aa,aa))
transforms=np.array([affine(i) for i in range(28)])
plan={0:('head','hair'),34:('head','face_neck'),14:('head','ornament'),20:('head','ornament'),25:('head','ornament'),30:('head','ornament'),31:('head','ornament'),37:('head','ornament'),29:('body','torso'),4:('body','sleeve'),5:('body','sleeve'),36:('body','hand'),38:('body','hand'),18:('body','panel'),21:('body','belt_tassel'),1:('legs','pants'),2:('legs','pants'),11:('legs','shoe'),15:('legs','shoe'),23:('legs','shoe'),27:('legs','shoe'),32:('legs','shoe'),35:('legs','shoe')}
bpy.ops.wm.read_factory_settings(use_empty=True)
# Recover the original 4K UV atlas by exact triangle correspondence. Tripo's
# segmentation retains all original faces but rebakes small low-resolution maps.
bpy.ops.import_scene.fbx(filepath=str(ROOT/'input/tripo_convert_1e91e0a9-4975-4e4d-b3a7-f926592b992a.fbx'),use_anim=False)
original=next(o for o in bpy.context.scene.objects if o.type=='MESH')
original.data.calc_loop_triangles();orig_uv=original.data.uv_layers.active.data
orig_points=[(original.matrix_world@v.co)/.978515923 for v in original.data.vertices]
tree=KDTree(len(orig_points))
for i,p in enumerate(orig_points):tree.insert(p,i)
tree.balance()
tri_uv={tuple(sorted(tri.vertices)): {original.data.loops[li].vertex_index:tuple(orig_uv[li].uv) for li in tri.loops} for tri in original.data.loop_triangles}
orig_triangles=[tuple(t.vertices) for t in original.data.loop_triangles]
bvh=BVHTree.FromPolygons(orig_points,orig_triangles,all_triangles=True)
original_texture=next(n.image for n in original.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
original_texture.filepath=str(ROOT/'tex/汉服女孩3d模型_basecolor.JPEG');original_texture.reload()
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'input/tripo_split/HanfuBlueRed_NoRig.fbx.fbx'),use_anim=False)
objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:int(o.name.rsplit('_',1)[1]))
assert len(objects)==len(plan)
uv_match_count=0;projected_count=0;position_error=0
for o in objects:
    mapping=[]
    for v in o.data.vertices:
        co,vi,dist=tree.find(o.matrix_world@v.co);mapping.append(vi);position_error=max(position_error,dist)
    assert position_error<.003,position_error
    for f in o.data.polygons:
        key=tuple(sorted(mapping[i] for i in f.vertices))
        if key in tri_uv:
            uvs=tri_uv[key]
            for li in f.loop_indices:o.data.uv_layers.active.data[li].uv=uvs[mapping[o.data.loops[li].vertex_index]]
        else:
            center=sum((o.matrix_world@o.data.vertices[i].co for i in f.vertices),Vector())/3
            nearest,normal,ti,distance=bvh.find_nearest(center);assert distance<.003,distance
            indices=orig_triangles[ti];uvs=tri_uv[tuple(sorted(indices))]
            a,b,c=[orig_points[i] for i in indices];ua,ub,uc=[Vector((*uvs[i],0)) for i in indices]
            for li in f.loop_indices:
                p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
                q=barycentric_transform(p,a,b,c,ua,ub,uc);o.data.uv_layers.active.data[li].uv=q[:2]
            projected_count+=1
        uv_match_count+=1
    mat=o.data.materials[0]
    for n in mat.node_tree.nodes:
        if n.type=='TEX_IMAGE':n.image=original_texture
assert uv_match_count==471354,uv_match_count
hair_surface_repairs=repair(objects)
del tri_uv,orig_points,tree
arrays={};seams={};records=[]
for o in objects:
    part_id=int(o.name.rsplit('_',1)[1]);slot,kind=plan[part_id]
    p=np.round(convert(np.array([o.matrix_world@v.co for v in o.data.vertices])),5)
    w=body_weights(p,use_arms=kind=='torso');alpha=np.zeros(len(p))
    if kind in {'hair','ornament'}:
        w[:]=0;w[:,13]=1
        if kind=='hair':alpha=.020*(1-smooth(.60*SCALE,.83*SCALE,p[:,2]))
    elif kind=='hand':
        sign=-1 if p[:,0].mean()<0 else 1;fore,hand=(17,19) if sign<0 else (24,26)
        axis=source[hand]-source[fore];t=((p-source[fore])@axis)/(axis@axis)
        blend=smooth(.85,1.01,t);w[:]=0;w[:,fore]=1-blend;w[:,hand]=blend
    elif kind=='shoe':
        # Each shoe surface piece is entirely on a single side.
        for sign,bone in [(-1,3),(1,7)]:
            ids=np.where(p[:,0]*sign>=0)[0];w[ids]=0;w[ids,bone]=1
    elif kind=='pants':
        w=body_weights(p,use_arms=False)
    elif kind=='sleeve':
        sign=-1 if p[:,0].mean()<0 else 1;upper,elbow=(15,17) if sign<0 else (22,24)
        arm=weights(p,[14,15,17,19] if sign<0 else [21,22,24,26])
        blend=smooth(.045*SCALE,.095*SCALE,np.abs(p[:,0]));w=w*(1-blend[:,None])+arm*blend[:,None]
        a=source[upper];axis=source[elbow]-a;t=np.clip((p-a)@axis/(axis@axis),0,1)
        below=(a+t[:,None]*axis)[:,2]-p[:,2]
        alpha=.025*smooth(.025,.17,below)
    elif kind=='panel':alpha=.024*(1-smooth(.31*SCALE,.59*SCALE,p[:,2]))
    elif kind=='belt_tassel':
        # Tassels retain waist anchors, rather than binding their tips to a calf.
        waist=np.zeros_like(w);waist[:,0]=1
        t=1-smooth(.57*SCALE,.63*SCALE,p[:,2]);w=w*(1-t[:,None])+waist*t[:,None]
        alpha=.035*(1-smooth(.31*SCALE,.61*SCALE,p[:,2]))
    w=normalize(w)
    name=f'hbr_{slot}_{part_id:02d}';arrays[name]={'S':p,'W':w,'A':alpha};o.name=name
    for vi,co in enumerate(p):seams.setdefault(tuple(co),[]).append((name,vi))
    records.append({'object':name,'source_part':part_id,'part':slot,'kind':kind,'material':f'hbr_part_{part_id:02d}','texture':Path(o.data.materials[0].node_tree.nodes.get('Image Texture').image.filepath).name if o.data.materials[0].node_tree.nodes.get('Image Texture') else None})
# All touching part boundaries share the same mapping and skin weights.
shared=0
record_by_name={r['object']:r for r in records}
detached_hair_points=0
for refs in seams.values():
    if len({n for n,i in refs})<2:continue
    if any(record_by_name[n]['kind']=='belt_tassel' and arrays[n]['S'][i,2]<.57*SCALE for n,i in refs):
        refs=[(n,i) for n,i in refs if record_by_name[n]['kind']!='belt_tassel']
        if len({n for n,i in refs})<2:continue
    # The source is a fused scan: hair touching clothing is not an anatomical
    # attachment. It must follow the head independently from the shoulder.
    if any(record_by_name[n]['part']=='head' and record_by_name[n]['kind'] in {'hair','ornament'} for n,i in refs) and any(record_by_name[n]['part']!='head' for n,i in refs):
        refs=[(n,i) for n,i in refs if record_by_name[n]['part']!='head'];detached_hair_points+=1
        if len({n for n,i in refs})<2:continue
    w=normalize(np.mean([arrays[n]['W'][i] for n,i in refs],axis=0)[None])[0]
    for n,i in refs:arrays[n]['W'][i]=w;arrays[n]['A'][i]=0
    shared+=1
bpy.ops.object.armature_add();rig=bpy.context.object;rig.name='human_skeleton'
bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones.remove(rig.data.edit_bones[0])
for i,n in enumerate(names):b=rig.data.edit_bones.new(n);b.matrix=Matrix(world[i].tolist());b.length=.045
for i,n in enumerate(names):
    if parent[i]>=0:rig.data.edit_bones[n].parent=rig.data.edit_bones[names[parent[i]]]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for o,rec in zip(objects,records):
    a=arrays[o.name];p,w,alpha=a['S'],a['W'],a['A'];d=np.zeros_like(p)
    for i in range(28):d+=w[:,i,None]*((p-source[i])@transforms[i].T+target[i])
    if rec['kind']=='hair':
        below=1-smooth(.70*SCALE,.86*SCALE,p[:,2])
        front=smooth(-.005*SCALE,.025*SCALE,p[:,1])
        contact=[Vector(k) for k,refs in seams.items() if any(n==o.name for n,i in refs) and any(n!=o.name and record_by_name[n]['part']=='head' for n,i in refs)]
        if contact:
            guard=KDTree(len(contact))
            for i,co in enumerate(contact):guard.insert(co,i)
            guard.balance();below*=smooth(0,.025,np.array([guard.find(Vector(co))[2] for co in p]))
        d[:,1]+=below*(front*.020-(1-front)*.010)
    a['P']=d;o.matrix_world=Matrix.Identity(4)
    for v,co in zip(o.data.vertices,d):v.co=co
    for f in o.data.polygons:f.use_smooth=True
    for i,n in enumerate(names):
        g=o.vertex_groups.new(name=n)
        for vi in np.where(w[:,i]>1e-6)[0]:g.add([int(vi)],float(w[vi,i]),'REPLACE')
    mod=o.modifiers.new('Native skin','ARMATURE');mod.object=rig;o.parent=rig
    attr=o.data.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
    colors=np.ones((len(p),4));colors[:,3]=alpha;attr.data.foreach_set('color',colors.ravel())
    o.data.color_attributes.active_color=attr
    mat=o.data.materials[0];mat.name=rec['material'];im=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    rec['texture']=Path(im.filepath).name
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.72
    rec.update(vertices=len(p),cloth=bool(alpha.max()>.001),max_distance=float(alpha.max()),bounds=[d.min(0).tolist(),d.max(0).tolist()])
shoe_leveling=level(objects,records,arrays,ROOT)
(ROOT/'reports/shoe_leveling.json').write_text(json.dumps(shoe_leveling,indent=2))
# Shared cut normals avoid visible shading changes at segmented skin and clothes.
ns={}
for o in objects:
    o.data.calc_loop_triangles()
    for tri in o.data.loop_triangles:
        v=[o.data.vertices[i] for i in tri.vertices];n=(v[1].co-v[0].co).cross(v[2].co-v[0].co)
        for x in v:
            key=tuple(round(c,5) for c in x.co);ns.setdefault(key,Vector((0,0,0)));ns[key]+=n
for o in objects:o.data.normals_split_custom_set_from_vertices([ns[tuple(round(c,5) for c in v.co)].normalized() for v in o.data.vertices])
for im in bpy.data.images:
    if im.source!='FILE':continue
    im.filepath=str(ROOT/'tex'/Path(im.filepath).name);im.reload();assert im.size[0]>0;im.pack()
rig['runtime_skeleton']='human_skeleton';rig['native_guid']=rigdata['guid']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
(ROOT/'build/rig_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
np.savez_compressed(ROOT/'build/rig_arrays.npz',source=source,target=target,world=world,**{n+'_'+k:v for n,a in arrays.items() for k,v in a.items()})
(ROOT/'reports/rig_fit.json').write_text(json.dumps({'source_scale':SCALE,'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'bone_names':names,'shared_boundary_points':shared,'detached_hair_clothing_points':detached_hair_points,'hair_surface_repairs':hair_surface_repairs,'restored_original_uv_triangles':uv_match_count,'projected_uv_triangles':projected_count,'original_correspondence_max_error':position_error,'parts':records},indent=2),encoding='utf-8')
print('RIG_READY',len(objects),'meshes',shared,'shared boundary points')
