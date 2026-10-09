"""Experimental inverse-bind compensation; no source limb length rescaling.

Runtime B assumes local scale matrices propagate through native hierarchy.
Runtime A assumes root scale propagates. Both assumptions need game probes.
"""
import bpy,json,sys,subprocess
import numpy as np
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[1];WS=R.parents[1]
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
rig=parse_skeljson(json.loads((R/'reports/human_skeleton.json').read_text()))
N=rig['restWorld'];L=rig['restLocal'];parent=rig['parent'];n=rig['boneCount'];assert n==28
T=N[:,:3,3];names=[name+'_'+str(i) for i,name in enumerate(rig['names'])]
S=np.zeros((n,3))
landmarks={0:[0,0,94],1:[-8.5,0,94],2:[-10.5,0,49],3:[-11,0,9],4:[-11,12,2],5:[8.5,0,94],6:[10.5,0,49],7:[11,0,9],8:[11,12,2],9:[0,0,108],10:[0,0,120],11:[0,0,132],12:[0,0,142],13:[0,0,151],14:[-7,0,133],15:[-15,0,133],17:[-32,0,114],19:[-45,0,101],20:[-51,0,95],21:[7,0,133],22:[15,0,133],24:[32,0,114],26:[45,0,101],27:[51,0,95]}
for i,p in landmarks.items():S[i]=np.array(p)*.01
for i,a,b in [(16,15,17),(18,17,19),(23,22,24),(25,24,26)]:S[i]=(S[a]+S[b])/2
nextbone={0:9,1:2,2:3,3:4,5:6,6:7,7:8,9:10,10:11,11:12,12:13,14:15,15:17,16:17,17:19,18:19,19:20,21:22,22:24,23:24,24:26,25:26,26:27}
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def weights(p,allowed):
 ds=[]
 for i in allowed:
  a=S[i];b=S[nextbone[i]] if i in nextbone else a+(a-S[parent[i]])*.5
  v=b-a;t=np.clip((p-a)@v/max(v@v,1e-10),0,1);ds.append(np.linalg.norm(p-a-t[:,None]*v,axis=1))
 ds=np.array(ds).T;v=np.exp(np.maximum(-(ds-ds.min(1,keepdims=True))/.035,-30));w=np.zeros((len(p),n));w[:,allowed]=v
 return w/w.sum(1,keepdims=True)
def normalize(w):
 keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;return w/w.sum(1,keepdims=True)
def skin(p,head=False):
 if head:
  w=np.zeros((len(p),n));w[:,13]=1;return w
 w=weights(p,[0,9,10,11,12]);lo=1-smooth(.88,1.01,p[:,2]);side=smooth(-.035,.035,p[:,0])
 leg=weights(p,[0,1,2,3])*(1-side[:,None])+weights(p,[0,5,6,7])*side[:,None];w=w*(1-lo[:,None])+leg*lo[:,None]
 for sign,ids in [(-1,[14,15,17,19]),(1,[21,22,24,26])]:
  selection=np.where(p[:,0]*sign>=0)[0];q=p[selection];blend=smooth(.08,.18,abs(q[:,0]))*smooth(.86,.94,q[:,2])
  w[selection]=w[selection]*(1-blend[:,None])+weights(q,ids)*blend[:,None]
 h=smooth(1.40,1.49,p[:,2]);w*=1-h[:,None];w[:,13]+=h
 return normalize(w)
def rotation(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=a@b
 k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
 return np.eye(3)+k+k@k/max(1+c,1e-8)
# Desired source-proportioned joint lengths, oriented along native rest chains.
D=N.copy();D[0,:3,3]=S[0]
for i in range(1,n):
 p=parent[i];direction=T[i]-T[p];length=np.linalg.norm(S[i]-S[p]);D[i,:3,3]=D[p,:3,3]+direction/max(np.linalg.norm(direction),1e-9)*length
rot=np.array([rotation(S[nextbone[i]]-S[i],D[nextbone[i],:3,3]-D[i,:3,3]) if i in nextbone else np.eye(3) for i in range(n)])
def world_scaled(scale):
 out=np.zeros_like(N)
 for i in range(n):
  local=L[i].copy();local[:3,:3]=local[:3,:3]@np.diag(scale[i]);out[i]=local if parent[i]<0 else out[parent[i]]@local
 return out
# Fit the actual modeled hierarchy numerically instead of approximating
# accumulated anisotropic scales by averages. Root remains uniformly 1.5.
adjustable=[i for i in range(1,n) if i in parent]
goal=N[0,:3,3]+(D[:,:3,3]-D[0,:3,3])*1.5
np.savez_compressed(R/'build/scale_fit_input.npz',native_local=L,parent=parent,goal=goal)
subprocess.run(['C:/ProgramData/anaconda3/python.exe','-B',str(R/'tools/fit_scales.py')],check=True)
scales=np.load(R/'build/scale_fit_output.npy')
profiles={'A':np.array([[1.5]*3]+[[1]*3]*(n-1)),'B':scales}
worlds={k:world_scaled(v) for k,v in profiles.items()}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');o.data.calc_loop_triangles();uv=o.data.uv_layers.active.data
raw=np.array([o.matrix_world@v.co for v in o.data.vertices]);P=raw*np.array([-1,-1,1])*.01
W=skin(P);record=[];source_rows=[]
# Save literal scaled source independently of the experimental game export.
for v,p in zip(o.data.vertices,P*1.5):v.co=p
o.matrix_world=Matrix.Identity(4)
for im in bpy.data.images:
 if im.source=='FILE':
  name=im.name.split('.png')[0]+'.png';path=R/'tex'/name
  if path.exists():im.filepath=str(path);im.reload();im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/Feifeng_Source_150.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/Feifeng_Source_150.fbx'),object_types={'MESH'},add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE')
# Repose uses rotations, not limb-length scaling. Head keeps original dimensions.
for slot in range(len(o.data.materials)):
 mat=o.data.materials[slot];tex=next(node.image.name.split('.png')[0]+'.png' for node in mat.node_tree.nodes if node.type=='TEX_IMAGE' and node.image)
 cut=slot in {0,2,4,5,7};source_rows.append(dict(slot=slot,texture=tex,cutout=cut))
 parts={}
 for tri in o.data.loop_triangles:
  if tri.material_index!=slot:continue
  center=P[list(tri.vertices)].mean(0)
  part='head' if slot in {4,5,6,7,8} else ('legs' if slot==2 or (slot==3 and center[2]<.90) else 'body')
  parts.setdefault(part,[]).append(tri)
 for part,tris in parts.items():
  ids=sorted({int(i) for tri in tris for i in tri.vertices});q=P[ids];w=skin(q,head=part=='head' and slot!=6);w=normalize(w)
  # Quantize before solving inverse blended matrices, so actual TPAC weights
  # match the compensation solver exactly.
  quant=np.floor(w*255).astype(int);quant[np.arange(len(w)),w.argmax(1)]+=255-quant.sum(1);w=quant/255.
  desired=np.zeros_like(q)
  for i in range(n):desired+=w[:,i,None]*((q-S[i])@rot[i].T+D[i,:3,3])
  desired*=1.5
  source_index={vi:i for i,vi in enumerate(ids)}
  for profile,world in worlds.items():
   transforms=world@np.linalg.inv(N);blend=np.einsum('vi,ijk->vjk',w,transforms);hp=np.concatenate([desired,np.ones((len(q),1))],axis=1)
   export=np.linalg.solve(blend,hp[...,None])[...,0][:,:3];recovered=np.einsum('vij,vj->vi',blend,np.concatenate([export,np.ones((len(q),1))],axis=1))[:,:3]
   assert np.max(abs(recovered-desired))<1e-8
   me=bpy.data.meshes.new(f'ffs_{profile}_{part}_{slot:02d}');me.from_pydata(export.tolist(),[],[[source_index[int(i)] for i in tri.vertices] for tri in tris]);me.update()
   ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat.copy())
   layer=me.uv_layers.new(name='UVMap')
   for f,tri in zip(me.polygons,tris):
    f.use_smooth=True
    for li,oldli in zip(f.loop_indices,tri.loops):layer.data[li].uv=uv[oldli].uv
   for i,name in enumerate(names):
    group=ob.vertex_groups.new(name=name)
    for vi in np.where(w[:,i]>0)[0]:group.add([int(vi)],float(w[vi,i]),'REPLACE')
   record.append(dict(object=ob.name,profile=profile,part=part,slot=slot,texture=tex,material=f'ffs_mat_{slot}',cloth=False,vertices=len(q)))
bpy.data.objects.remove(o,do_unlink=True)
# Native armature records the export binding; the source dimensions are in the
# separate Source_150 file and reconstructed runtime prediction.
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name='human_skeleton';bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0])
for i,name in enumerate(names):b=arm.data.edit_bones.new(name);b.matrix=Matrix(N[i].tolist());b.length=.04
for i,name in enumerate(names):
 if parent[i]>=0:arm.data.edit_bones[name].parent=arm.data.edit_bones[names[parent[i]]]
bpy.ops.object.mode_set(mode='OBJECT')
for row in record:
 ob=bpy.data.objects[row['object']];modifier=ob.modifiers.new('Native binding','ARMATURE');modifier.object=arm;ob.parent=arm
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/Feifeng_Test_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/Feifeng_Test_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='RELATIVE')
(R/'build/rig_manifest.json').write_text(json.dumps(record,indent=2));(R/'build/material_plan.json').write_text(json.dumps(source_rows,indent=2))
report=dict(source_multiplier=1.5,source_cm_to_m=.01,source_total_height_m=float(np.ptp(P[:,2])*1.5),source_landmarks_m=S.tolist(),manual_landmarks=True,limb_fit='rotation only; no longitudinal stretch',runtime_convention='experimental local diagonal hierarchy; unverified in engine',joint_fit_max_error_m=float(np.linalg.norm(worlds['B'][:,:3,3]-goal,axis=1).max()),profiles={k:v.tolist() for k,v in profiles.items()},expected_rest_positions={k:v[:,:3,3].tolist() for k,v in worlds.items()})
(R/'reports/scale_plan.json').write_text(json.dumps(report,indent=2))
np.savez_compressed(R/'build/rig_data.npz',native_world=N,desired_world=D,source_landmarks=S,**{'world_'+k:v for k,v in worlds.items()})
print('RIG_READY',len(record),'parts; source 150 percent height',report['source_total_height_m'])
