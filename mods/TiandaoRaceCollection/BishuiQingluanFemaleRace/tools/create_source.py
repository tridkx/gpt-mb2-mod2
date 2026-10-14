"""Preserve source proportions, fit native semantic joints and author cloth roots."""
import bpy,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
from skirt_policy import travel as hem_travel,reference_weights
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
raw=json.loads((R/'reports/human_skeleton.json').read_text());rig=parse_skeljson(raw)
cfg=json.loads((R/'tools/model_config.json').read_text());S=np.array(cfg['landmarks_m']);world=rig['restWorld'].copy();world[:,:3,3]=S
for i,start,end in [(15,15,17),(16,15,17),(17,17,19),(18,17,19),(22,22,24),(23,22,24),(24,24,26),(25,24,26)]:
 a=world[i,:3,0];v=S[end]-S[start];v/=np.linalg.norm(v);cross=np.cross(a,v);c=float(a@v);K=np.array([[0,-cross[2],cross[1]],[cross[2],0,-cross[0]],[-cross[1],cross[0],0]])
 world[i,:3,:3]=(np.eye(3)+K+K@K/(1+c))@world[i,:3,:3]
local=np.array([world[i] if p<0 else np.linalg.inv(world[p])@world[i] for i,p in enumerate(rig['parent'])]);bones=[]
for i,b in enumerate(raw['bones']):
 m=np.array(b['rest']).reshape(4,4).T;m[:3,:3]=local[i,:3,:3];m[:3,3]=local[i,:3,3];bones.append(dict(name=b['name'],parent=b['parent'],rest=m.T.ravel().tolist()))
(R/'build/skeleton_spec.json').write_text(json.dumps(bones,indent=2))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
objects=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name);parts=json.loads((R/'input/parts.json').read_text())
nextbone={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,17:19,19:20,21:22,22:24,24:26,26:27}
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def near(p,ids):
 ds=[]
 for i in ids:
  a=S[i];b=S[nextbone[i]] if i in nextbone else a+np.array([0,0,.05]);v=b-a;t=np.clip((p-a)@v/max(v@v,1e-10),0,1);ds.append(np.linalg.norm(p-a-t[:,None]*v,axis=1))
 ds=np.array(ds).T;v=np.exp(np.maximum(-(ds-ds.min(1,keepdims=True))/.026,-25));w=np.zeros((len(p),28));w[:,ids]=v;return w/w.sum(1,keepdims=True)
def body(p):
 w=near(p,[0,9,10,11,12]);lo=1-smooth(.94,1.05,p[:,2]);side=smooth(-.065,.065,p[:,0]);legs=near(p,[0,1,2,3,4])*(1-side[:,None])+near(p,[0,5,6,7,8])*side[:,None];w=w*(1-lo[:,None])+legs*lo[:,None]
 for sign,ids in [(-1,[14,15,17,19]),(1,[21,22,24,26])]:
  ix=np.where(p[:,0]*sign>=0)[0];a=smooth(.11,.19,abs(p[ix,0]))*smooth(1.03,1.16,p[ix,2]);w[ix]=w[ix]*(1-a[:,None])+near(p[ix],ids)*a[:,None]
 h=smooth(1.415,1.45,p[:,2])*(1-smooth(.06,.10,abs(p[:,0])));w*=1-h[:,None];w[:,13]+=h;return w
def components(o,p):
 keys={};owner=[]
 for v in np.round(p,6):
  k=tuple(v);keys.setdefault(k,len(keys));owner.append(keys[k])
 parent=list(range(len(keys)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for e in o.data.edges:a,b=e.vertices;parent[root(owner[a])]=root(owner[b])
 roots=sorted({root(x) for x in owner});return np.array([roots.index(root(x)) for x in owner])
positions={};weights={};paint=[];manifest=[];materials={};alphas={};skirtflags={}
for oi,o in enumerate(objects):
 old=o.name;row=next(r for r in parts if r['name']==old);tex=row['tex'];p=np.array([o.matrix_world@v.co for v in o.data.vertices])*.01;positions[old]=p;w=body(p);a=np.zeros(len(p));labels=components(o,p);comps=[];skirtflag=np.zeros(len(p),bool)
 head=tex in ['head5_eye','head5_face','head5_eyelash','hair','head']
 if head:w[:]=0;w[:,13]=1
 for c in sorted(set(labels)):
  ids=np.flatnonzero(labels==c);q=p[ids];lo=q.min(0);hi=q.max(0);kind='skin'
  if tex=='cloth' and oi==9:
   if lo[2]<.45 and hi[2]-lo[2]>.20:
    kind='skirt';sk=q[:,2]<1.045;skirtflag[ids]=sk;lower=reference_weights(q,cfg['mapped_cloth']['hem_policy']);w[ids[sk]]=lower[sk];a[ids]=np.where(sk,hem_travel(q[:,2],cfg['mapped_cloth']['hem_policy']),0)
   elif hi[2]-lo[2]>.15 and hi[2]<1.2:
    kind='ribbon';w[ids]=0;w[ids,0]=1;travel=np.maximum(hi[2]-.035-q[:,2],0)*.12;a[ids]=np.minimum(travel,.06)
  if tex=='cloth' and oi==13:
   sign=-1 if q[:,0].mean()<0 else 1;idsbones=[14,15,17,19] if sign<0 else [21,22,24,26];w[ids]=near(q,idsbones);kind='sleeve'
   # Distance from the anatomical arm defines hanging cloth, not height alone.
   armA=S[15 if sign<0 else 22];armB=S[19 if sign<0 else 26];axis=armB-armA;t=np.clip((q-armA)@axis/(axis@axis),0,1);distance=np.linalg.norm(q-armA-t[:,None]*axis,axis=1)
   a[ids]=np.minimum(np.maximum(distance-.075,0)*.9,.65) if cfg.get('sleeve_cloth_enabled',False) else 0
   # The attachment direction includes the cuff and shoulder seam.
   a[ids[q[:,2]>1.30]]=0
  if tex=='hair' and hi[2]-lo[2]>.2:
   kind='hair';a[ids]=np.minimum(np.maximum(hi[2]-.07-q[:,2],0)*.065,.035)
  if tex=='head' and hi[2]-lo[2]>.20:
   kind='ornament';a[ids]=np.minimum(np.maximum(hi[2]-.03-q[:,2],0)*.08,.035)
  if tex in ['head5_body','hand'] and abs(q[:,0].mean())>.25:
   w[ids]=near(q,[15,17,19] if q[:,0].mean()<0 else [22,24,26])
  comps.append(dict(component=int(c),kind=kind,vertices=len(ids),bbox_m=[lo.tolist(),hi.tolist()],active=int((a[ids]>0).sum())))
 weights[old]=w;alphas[old]=a;skirtflags[old]=skirtflag;name='bql_part_'+str(oi).zfill(2);o.name=name
 manifest.append(dict(object=name,source_object=old,part='body',material=tex,kind='hair' if head else 'body'))
 paint.append(dict(object=name,components=comps))
 materials[tex]=dict(diffuse=tex+'.png',normal=None,specular=None,cutout=row['alpha'])
# Equal weights at shared positions prevent source material seams opening.
pts=np.concatenate(list(positions.values()));ww=np.concatenate(list(weights.values()));unique,owner=np.unique(np.round(pts,5),axis=0,return_inverse=True);avg=np.zeros((len(unique),28));np.add.at(avg,owner,ww);avg/=np.bincount(owner)[:,None];ww=avg[owner]
keep=np.argsort(-ww,axis=1)[:,:4];mask=np.zeros_like(ww);np.put_along_axis(mask,keep,1,1);ww*=mask;ww/=ww.sum(1,keepdims=True)
if cfg.get('coherent_sleeve_skinning'):
 from sleeve_skinning import apply
 key=manifest[13]['source_object'];start=sum(len(positions[rec['source_object']]) for rec in manifest[:13]);count=len(positions[key]);others=np.concatenate([v for k,v in positions.items() if k!=key]);ww[start:start+count],_=apply(positions[key],ww[start:start+count],others)
names=[n+'_'+str(i) for i,n in enumerate(rig['names'])];offset=0;arrays={}
for o,rec in zip(objects,manifest):
 old=rec['source_object'];p=positions[old];w=ww[offset:offset+len(p)];offset+=len(p)
 for v,co in zip(o.data.vertices,p):v.co=co
 o.matrix_world=Matrix.Identity(4)
 for g in list(o.vertex_groups):o.vertex_groups.remove(g)
 for i,n in enumerate(names):
  group=o.vertex_groups.new(name=n)
  for vi in np.flatnonzero(w[:,i]>1e-7):group.add([int(vi)],float(w[vi,i]),'REPLACE')
 o.data.calc_loop_triangles();arrays[o.name+'_p']=p;arrays[o.name+'_w']=w;arrays[o.name+'_f']=np.array([list(t.vertices) for t in o.data.loop_triangles],dtype='i4')
 arrays[o.name+'_sk']=skirtflags[old]
 layer=o.data.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
 for vi in range(len(p)):layer.data[vi].color=(1,1,1,float(alphas[old][vi]))
 tex=rec['material'];mat=bpy.data.materials.new('bql_'+tex.lower());mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65;img=bpy.data.images.load(str(R/'tex'/(tex+'.png')),check_existing=True);img.pack();node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
 if materials[tex]['cutout']:mat.node_tree.links.new(node.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
 o.data.materials.clear();o.data.materials.append(mat)
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name=cfg['skeleton'];bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0])
for i,n in enumerate(names):b=arm.data.edit_bones.new(n);b.matrix=Matrix(world[i].tolist());b.length=.04
for i,n in enumerate(names):
 if rig['parent'][i]>=0:arm.data.edit_bones[n].parent=arm.data.edit_bones[names[rig['parent'][i]]]
bpy.ops.object.mode_set(mode='OBJECT')
for o in objects:mod=o.modifiers.new('Race binding','ARMATURE');mod.object=arm;o.parent=arm
(R/'build/manifest.json').write_text(json.dumps(manifest,indent=2));np.savez_compressed(R/'build/fitted_model.npz',**arrays);(R/'tex/materials.json').write_text(json.dumps(materials,indent=2));(R/'reports/cloth_paint.json').write_text(json.dumps(paint,indent=2))
(R/'reports/weight_transfer.json').write_text(json.dumps(dict(native_bones=rig['names'],source_landmarks=S.tolist(),source_geometry_max_error_m=0,source_proportions_preserved=True,height_m=float(np.ptp(pts[:,2])),unit_scale=.01,arm_bind_axes_aligned=True),indent=2))
(R/'reports/input_hashes.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'input').rglob('*') if p.is_file()},indent=2,ensure_ascii=False))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/BishuiQingluanFemaleRace_Rigged.blend'));bpy.ops.export_scene.fbx(filepath=str(R/'source/BishuiQingluanFemaleRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
print('SOURCE_READY',len(manifest),pts.min(0),pts.max(0))
