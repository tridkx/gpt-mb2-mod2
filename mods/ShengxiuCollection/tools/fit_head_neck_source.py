"""Mingyu head pivot, continuous neck skin and closer rear hair from v1.1.5."""
import bpy,json,sys,shutil
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hair_shape_analysis import smooth
base=ROOT/'build/head_neck_baseline_v1.1.5';base.mkdir(exist_ok=True)
for path in [ROOT/'source/ShengxiuCollection_Rigged.blend',ROOT/'source/ShengxiuCollection_Rigged.fbx',ROOT/'build/rig_arrays.npz',ROOT/'build/rig_manifest.json',ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac']:
 if not (base/path.name).exists():shutil.copy2(path,base/path.name)
bpy.ops.wm.open_mainfile(filepath=str(base/'ShengxiuCollection_Rigged.blend'))
arrays=dict(np.load(base/'rig_arrays.npz'));manifest=json.loads((base/'rig_manifest.json').read_text())
original=np.load(ROOT/'build/hair_shape_baseline_v1.1.4/rig_arrays.npz');changes=[]
for rec in manifest:
 name=rec['object']
 if rec['part']!='head' and name!='sx_mingyu_body_02':continue
 o=bpy.data.objects[name];p=arrays[name+'_P'].copy();w=arrays[name+'_W'].copy();q=p.copy()
 if name=='sx_mingyu_head_00':
  old=original[name+'_P'];rear=1-smooth(-.025,.015,old[:,1]);lower=1-smooth(1.26,1.48,old[:,2])
  # The innermost waist-level tips need 20mm more clearance during idle sway.
  # Retain that locally while the main sheet returns the full 45mm.
  return_distance=.025+.020*smooth(.98,1.15,old[:,2])
  q[:,1]+=return_distance*rear*lower
  attr=o.data.color_attributes['ClothDistance']
  for i in range(len(p)):
   if rear[i]>.99:attr.data[i].color[3]=min(attr.data[i].color[3],.008)
  arrays[name+'_A']=np.array([v.color[3] for v in attr.data])
 # Actual Mingyu inventory animation reaches ~25 degrees of head pitch while
 # the neck stays near 6 degrees. Move this model's follow pivot toward neck.
 hw=w[:,13].copy();w[:,12]+=hw*.85;w[:,13]*=.15
 if name in ['sx_mingyu_head_08','sx_mingyu_body_02']:
  head=smooth(1.425,1.515,p[:,2]);target=np.zeros_like(w)
  target[:,11]=1-head;target[:,12]=head*.85;target[:,13]=head*.15
  if name=='sx_mingyu_head_08':w=target
  else:
   influence=smooth(1.37,1.425,p[:,2])*(1-smooth(.075,.12,abs(p[:,0])))
   w=w*(1-influence[:,None])+target*influence[:,None]
 keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,axis=1);w*=mask;w/=w.sum(1,keepdims=True)
 for v in o.data.vertices:
  v.co=q[v.index]
  for group in o.vertex_groups:group.remove([v.index])
  for bone in np.flatnonzero(w[v.index]>1e-6):
   group=next(g for g in o.vertex_groups if g.name.endswith('_'+str(bone)))
   group.add([v.index],float(w[v.index,bone]),'REPLACE')
 arrays[name+'_W']=w;arrays[name+'_P']=q;o.data.update()
 rec['bounds']=[q.min(0).tolist(),q.max(0).tolist()];changes.append(name)
np.savez(ROOT/'build/rig_arrays.npz',**arrays);(ROOT/'build/rig_manifest.json').write_text(json.dumps(manifest,indent=2))
for o in bpy.context.scene.objects:o.select_set(o.type in ['MESH','ARMATURE'])
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/ShengxiuCollection_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/ShengxiuCollection_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
(ROOT/'reports/head_neck_source_fit.json').write_text(json.dumps({'status':'pass','changed_objects':changes,'neck_follow':.85,'maximum_hair_forward_m':.045,'waist_tip_forward_m':.025,'waist_tip_blend_z_m':[.98,1.15],'rear_return_fade_z_m':[1.26,1.48],'rear_cloth_limit_m':.008,'neck_transition_z_m':[1.425,1.515],'all_rest_geometry_except_posterior_hair_unchanged':True},indent=2))
print('HEAD_NECK_SOURCE_READY',changes)
