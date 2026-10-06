import bpy, os, sys, json, re, math
import numpy as np
from mathutils import Vector, Matrix
ROOT=r'D:\gpt-mb2-mod2'
sys.path.insert(0,ROOT+'/tools')
from motion_fit import forward_arms,skirt_weights,skirt_clearance,ARM_FORWARD_DEGREES
OUT=os.path.join(ROOT,'build')
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=ROOT+'/inspection.blend')
src_objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
raw=json.load(open(ROOT+'/reports/human_skeleton.json'))
parent=np.array([b['parent'] for b in raw['bones']])
world=[]
for b in raw['bones']:
 L=np.array(b['rest']).reshape(4,4).T;L[3]=[0,0,0,1]
 world.append(L if b['parent']<0 else world[b['parent']]@L)
world=np.array(world);target=world[:,:3,3]
source=np.zeros((28,3))
# Locate chest joints below the clavicles. The previous spine2 landmark sat at
# shoulder height, stretching the chest-to-neck segment and folding the collar.
for i,p in {0:(0,0,.965),9:(0,-.004,1.066),10:(0,-.008,1.160),11:(0,-.01,1.285),12:(0,-.014,1.437),13:(0,.003,1.542)}.items():source[i]=p
for ids,sign in [([1,2,3,4,14,15,16,17,18,19,20],-1),([5,6,7,8,21,22,23,24,25,26,27],1)]:
 points=[(.085,0,.965),(.112,-.012,.525),(.117,-.025,.082),(.118,.091,.003),(.04,-.025,1.366),(.155,-.025,1.366),(.230,-.012,1.260),(.305,0,1.154),(.365,.012,1.094),(.425,.024,1.034),(.469,.038,.978)]
 for i,p in zip(ids,points):source[i]=[sign*p[0],p[1],p[2]]
nxt={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,17:19,19:20,21:22,22:24,24:26,26:27}
names=['bip01_'+b['name']+'_'+str(b['i']) for b in raw['bones']]
bpy.ops.object.armature_add()
rig=bpy.context.object;rig.name='human_skeleton_notused'
bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones.remove(rig.data.edit_bones[0])
for i,nm in enumerate(names):
 b=rig.data.edit_bones.new(nm);b.matrix=Matrix(world[i].tolist());b.length=.055
for i,nm in enumerate(names):
 if parent[i]>=0:rig.data.edit_bones[nm].parent=rig.data.edit_bones[names[parent[i]]]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def weights(P,allowed):
 ds=[]
 for i in allowed:
  a=source[i];end=source[nxt[i]] if i in nxt else a+(a-source[parent[i]])*.8
  axis=end-a;t=np.clip(((P-a)@axis)/max(axis@axis,1e-10),0,1)
  d=np.linalg.norm(P-(a+t[:,None]*axis),axis=1)
  ds.append(d)
 ds=np.array(ds).T
 # Narrow smooth capsule blend, with support at joints, without remote-bone influence.
 logw=-(ds-ds.min(1,keepdims=True))/.027
 w=np.exp(np.maximum(logw,-25));w[w<.025]=0
 W=np.zeros((len(P),28));W[:,allowed]=w
 keep=np.argsort(-W,axis=1)[:,:4];mask=np.zeros_like(W);np.put_along_axis(mask,keep,1,1);W*=mask
 return W/np.maximum(W.sum(1,keepdims=True),1e-12)
def affine(i):
 M=np.eye(3)
 if i in nxt:
  a=source[nxt[i]]-source[i];b=target[nxt[i]]-target[i]
  aa=a/np.linalg.norm(a);bb=b/np.linalg.norm(b);v=np.cross(aa,bb);c=aa@bb
  K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
  R=np.eye(3)+K+K@K/max(1+c,1e-8)
  M=R@(np.eye(3)+(np.linalg.norm(b)/np.linalg.norm(a)-1)*np.outer(aa,aa))
 return M
transform=[affine(i) for i in range(28)]
def body_weights(P,use_arms=True):
 torso=weights(P,[0,9,10,11,12]);out=torso.copy()
 for sign,arm,leg in [(-1,[14,15,17,19],[0,1,2,3,4]),(1,[21,22,24,26],[0,5,6,7,8])]:
  ids=np.where((P[:,0]*sign)>=0)[0];Q=P[ids]
  if not len(ids):continue
  armblend=smooth(.095,.205,np.abs(Q[:,0])) if use_arms else np.zeros(len(ids))
  upper=torso[ids]
  legblend=1-smooth(.96,1.10,Q[:,2]);lower=weights(Q,leg)
  base=upper*(1-legblend[:,None])+lower*legblend[:,None]
  out[ids]=base*(1-armblend[:,None])+weights(Q,arm)*armblend[:,None]
 # Use the same neck transition in the face, skin and collar meshes. Original
 # duplicate vertices at the head/body boundary must share identical weights.
 h=smooth(1.405,1.475,P[:,2])*(1-smooth(.055,.095,np.abs(P[:,0])))
 out*=1-h[:,None];out[:,13]+=h
 return out

def neck_shape(P,D,whole_head=False):
 # Raise the chest through the corrected landmarks above and shorten the
 # remaining exposed neck by 14 mm, preserving the face and head proportions.
 blend=np.ones(len(P)) if whole_head else smooth(1.355,1.475,P[:,2])*(1-smooth(.055,.095,np.abs(P[:,0])))
 D[:,2]-=.014*blend
 return D
def components(me):
 p=list(range(len(me.vertices)))
 def root(a):
  while p[a]!=a:p[a]=p[p[a]];a=p[a]
  return a
 for e in me.edges:
  a,b=e.vertices;p[root(a)]=root(b)
 groups={}
 for i in range(len(p)):groups.setdefault(root(i),[]).append(i)
 return list(groups.values())
head_ids={1,2,9,10,11,12,13};body_ids={0,3,4,7,8};legs_ids={5,6}
records=[];all_arrays={}
for oi,o in enumerate(src_objects):
 # A 10-micron grid gives coincident source seams exactly identical positions
 # and skinning weights, including vertices split into different equipment.
 P=np.round(np.array([o.matrix_world@v.co for v in o.data.vertices])*.01,5)
 W=body_weights(P,use_arms=oi not in {3,5,6});A=np.zeros(len(P));kind=np.empty(len(P),object)
 for ids in components(o.data):
  ids=np.array(ids);Q=P[ids];lo=Q.min(0);hi=Q.max(0);mid=Q.mean(0);sign=-1 if mid[0]<0 else 1
  arm=[14,15,17,19] if sign<0 else [21,22,24,26]
  leg=[0,1,2,3,4] if sign<0 else [0,5,6,7,8]
  if oi in head_ids:
   if oi not in {9,11}:
    # Do not retain the initial torso weights on rigid head parts.
    W[ids]=0;W[ids,13]=1
   kind[ids]='head'
   if oi==1:
    A[ids]=.028*smooth(1.43,1.05, Q[:,2])
    # Hair remains anchored to the head. Its lower lengths receive only limited physics.
    kind[ids]='hair'
  elif oi in legs_ids:
   kind[ids]='leg'
  elif oi==3:
   if lo[2]<.5:
    A[ids]=.040*smooth(.95,.28,Q[:,2]);kind[ids]='skirt'
   else:kind[ids]='waist'
  elif oi==0 and lo[2]<.6 and abs(mid[0])>.20:
   # Long sleeve streamers must follow their sleeve root throughout their length.
   W[ids]=0;W[ids,15 if sign<0 else 22]=1
   A[ids]=.11*smooth(1.18,.58,Q[:,2]);kind[ids]='streamer'
  elif oi in {7,8} or (abs(mid[0])>.125 and hi[2]>1.14):
   kind[ids]='arm'
   if oi==0:
    # Keep sleeve seam pinned; allow a small movement at the hanging edge.
    a=source[15 if sign<0 else 22];b=source[17 if sign<0 else 24];axis=b-a
    t=np.clip(((Q-a)@axis)/(axis@axis),0,1);axis_z=(a+t[:,None]*axis)[:,2]
    A[ids]=.03*smooth(.055,.18,axis_z-Q[:,2])
  else:
   kind[ids]='torso'
 # Force matching seam vertices to matching weights within each source piece.
 seams={}
 for vi,p in enumerate(P):seams.setdefault(tuple(np.round(p,5)),[]).append(vi)
 for ids in seams.values():
  if len(ids)>1:W[ids]=W[ids].mean(0);A[ids]=A[ids].mean()
 # Limit weights again after seam averaging.
 keep=np.argsort(-W,axis=1)[:,:4];mask=np.zeros_like(W);np.put_along_axis(mask,keep,1,1);W*=mask;W/=W.sum(1,keepdims=True)
 D=np.zeros_like(P)
 for i in range(28):D+=W[:,i,None]*((P-source[i])@transform[i].T+target[i])
 # Streamers use a rigid, length-preserving rotation around their attachment.
 for ids in components(o.data):
  ids=np.array(ids)
  if kind[ids[0]]=='streamer':
   Q=P[ids];bone=15 if Q[:,0].mean()<0 else 22
   anchor=Q[np.argmax(Q[:,2])];aw=body_weights(anchor[None,:]);mapped=np.zeros(3)
   for i in range(28):mapped+=aw[0,i]*((anchor-source[i])@transform[i].T+target[i])
   a=source[nxt[bone]]-source[bone];b=target[nxt[bone]]-target[bone]
   aa=a/np.linalg.norm(a);bb=b/np.linalg.norm(b);v=np.cross(aa,bb);c=aa@bb;K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
   R=np.eye(3)+K+K@K/max(1+c,1e-8);D[ids]=(Q-anchor)@R.T+mapped
 if oi in head_ids:
  # The face's lower neck and neck accessories use the common skin transition.
  # Eyes, lashes, hair and ornaments remain rigidly attached to the head.
  if oi not in {9,11}:D=P-source[13]+target[13]
 D=neck_shape(P,D,whole_head=oi in head_ids and oi not in {9,11})
 # Shoulder-centered forward rotation shared by skin, sleeves and ornaments.
 D=forward_arms(D,W,target)
 if oi in {0,3}:
  # Small radial clearance on free fabric, away from legs and torso.
  free=A>0.003;rad=D[:,:2].copy();rad[:,1]-=0.02
  rad/=np.maximum(np.linalg.norm(rad,axis=1,keepdims=True),1e-6)
  D[free,:2]+=rad[free]*.008
 if oi==1:D[:,1]-=.007*smooth(1.45,1.05,P[:,2])
 if oi==3:
  # Keep the waist on the pelvis, then follow thighs before the knee can enter
  # the front panels. Gradually transfer the lower portion to same-side calves.
  # The continuous center blend keeps the connected back panel joined.
  Q=P
  W=skirt_weights(Q,weights(Q,[0,9,10]))
  D=skirt_clearance(D,Q)
  # Small detached surface patches receive the same spatial mask as the main skirt.
  A=np.maximum(A,.040*smooth(.94,.30,Q[:,2]))
 o.matrix_world=Matrix.Identity(4)
 for v,co in zip(o.data.vertices,D):v.co=co
 for p in o.data.polygons:p.use_smooth=True
 for i,nm in enumerate(names):
  vg=o.vertex_groups.new(name=nm)
  for vi in np.where(W[:,i]>1e-5)[0]:vg.add([int(vi)],float(W[vi,i]),'REPLACE')
 mod=o.modifiers.new('Bannerlord Skin','ARMATURE');mod.object=rig
 o.parent=rig
 attr=o.data.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
 for vi,c in enumerate(attr.data):c.color=(1,1,1,float(A[vi]))
 o.data.color_attributes.active_color=attr
 part='head' if oi in head_ids else 'body' if oi in body_ids else 'legs'
 short=['tunic','hair','hair','tunic','skin','pants','cuff','skin','skin','head','head','face','eye','lash'][oi]
 o.name='tx5_'+part+'_'+str(oi).zfill(2)
 o['source_object']=src_objects[oi].get('source_object',str(oi));o['cloth_max_distance']=float(A.max())
 records.append({'object':o.name,'source_index':oi,'part':part,'material':'tx5_'+short,'cloth':bool(A.max()>.001),'vertices':len(P),'simulated_vertices':int((A>.001).sum()),'max_distance':float(A.max()),'bounds':[D.min(0).tolist(),D.max(0).tolist()]})
 all_arrays[o.name]={'P':D,'S':P,'W':W,'A':A}
 # Make the Blender material reflect the intended game alpha semantics.
 m=o.data.materials[0];m.name='tx5_'+short+'_preview_'+str(oi)
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.68;bs.inputs['Metallic'].default_value=0
 if short in {'tunic','pants'}:
  for link in list(bs.inputs['Alpha'].links):m.node_tree.links.remove(link)
  bs.inputs['Alpha'].default_value=1
# Smooth UV-split skin vertices, including the shared face/body neck boundary.
# Topology and UVs remain separate; only shading normals are shared.
skin_objects=[src_objects[i] for i in [4,7,11]]
normal_sums={}
for o in skin_objects:
 me=o.data;me.calc_loop_triangles()
 for tri in me.loop_triangles:
  verts=[me.vertices[i] for i in tri.vertices]
  normal=(verts[1].co-verts[0].co).cross(verts[2].co-verts[0].co)
  for v in verts:
   key=tuple(round(c,5) for c in v.co)
   normal_sums.setdefault(key,Vector((0,0,0)));normal_sums[key]+=normal
for o in skin_objects:
 normals=[normal_sums[tuple(round(c,5) for c in v.co)].normalized() for v in o.data.vertices]
 o.data.normals_split_custom_set_from_vertices(normals)
for img in bpy.data.images:
 if img.source!='FILE':continue
 texture_path=os.path.join(ROOT,'tex',os.path.basename(img.filepath.replace('\\','/')))
 if not os.path.isfile(texture_path):
  texture_path=os.path.join(ROOT,'tex',re.sub(r'\.\d{3}$','',img.name))
 if not os.path.isfile(texture_path):raise FileNotFoundError(texture_path)
 # Background loading is lazy. Load pixels explicitly before packing, otherwise
 # has_data is false and the delivered .blend depends on relative texture paths.
 img.filepath=texture_path;img.reload();img.pack()
 assert img.packed_file is not None,img.name
# Add disabled Blender cloth previews. They are separate from game physics metadata.
preview=bpy.data.collections.new('Blender Cloth Preview - optional');bpy.context.scene.collection.children.link(preview)
for o,rec in zip(src_objects,records):
 if not rec['cloth']:continue
 c=o.copy();c.data=o.data.copy();c.name=o.name+'_cloth_preview';preview.objects.link(c)
 pin=c.vertex_groups.new(name='ClothPin')
 A=all_arrays[o.name]['A'];maximum=max(A.max(),.001)
 for vi,a in enumerate(A):pin.add([vi],float(1-a/maximum),'REPLACE')
 cloth=c.modifiers.new('Optional Blender Cloth','CLOTH');cloth.settings.quality=8;cloth.settings.mass=.22
 cloth.settings.vertex_group_mass=pin.name;cloth.settings.tension_stiffness=40;cloth.settings.compression_stiffness=40
 cloth.settings.shear_stiffness=25;cloth.settings.bending_stiffness=2;cloth.settings.air_damping=4
 cloth.collision_settings.use_self_collision=True;cloth.collision_settings.distance_min=.006;cloth.collision_settings.self_distance_min=.004;cloth.collision_settings.collision_quality=6
 c.hide_render=True;c.hide_set(True)
preview.hide_render=True;preview.hide_viewport=True
rig['runtime_skeleton']='human_skeleton';rig['bone_count']=28
rig['arm_forward_degrees']=ARM_FORWARD_DEGREES
os.makedirs(ROOT+'/source',exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/source/TianxiangT5_Rigged.blend')
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in src_objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=ROOT+'/source/TianxiangT5_Rigged.fbx',use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',colors_type='LINEAR',use_mesh_modifiers=False)
with open(OUT+'/rig_manifest.json','w',encoding='utf-8') as f:json.dump(records,f,ensure_ascii=False,indent=2)
np.savez_compressed(OUT+'/rig_arrays.npz',source=source,target=target,world=world,**{k+'_'+a:v for k,d in all_arrays.items() for a,v in d.items()})
print('RIG_READY',sum(r['vertices'] for r in records),'vertices')
