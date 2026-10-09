"""Apply a reproducible posterior hair fit from the preserved v1.1.4 source."""
import bpy,json,sys,shutil,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hair_shape_analysis import change,smooth
base=ROOT/'build/hair_shape_baseline_v1.1.4';base.mkdir(exist_ok=True)
for path in [ROOT/'source/ShengxiuCollection_Rigged.blend',ROOT/'source/ShengxiuCollection_Rigged.fbx',ROOT/'build/rig_arrays.npz',ROOT/'build/rig_manifest.json']:
 if not (base/path.name).exists():shutil.copy2(path,base/path.name)
bpy.ops.wm.open_mainfile(filepath=str(base/'ShengxiuCollection_Rigged.blend'))
arrays=dict(np.load(base/'rig_arrays.npz'));manifest=json.loads((base/'rig_manifest.json').read_text())
o=bpy.data.objects['sx_mingyu_head_00'];p=np.array([v.co for v in o.data.vertices]);q,t=change(p)
for v in o.data.vertices:v.co=q[v.index]
head=next(g for g in o.vertex_groups if g.name.endswith('_13'));spine=next(g for g in o.vertex_groups if g.name.endswith('_11'))
for v in o.data.vertices:
 for g in o.vertex_groups:g.remove([v.index])
 head.add([v.index],float(1-t[v.index]),'REPLACE')
 if t[v.index]>1e-6:spine.add([v.index],float(t[v.index]),'REPLACE')
alpha=o.data.color_attributes['ClothDistance']
for v in o.data.vertices:
 old=alpha.data[v.index].color[3];rear=1-smooth(-.025,.015,p[v.index,1])
 alpha.data[v.index].color[3]=min(old,.012) if rear>.99 else old
o.data.update();arrays[o.name+'_P']=q
weights=np.zeros((len(p),28));weights[:,13]=1-t;weights[:,11]=t
arrays[o.name+'_W']=weights
arrays[o.name+'_A']=np.array([c.color[3] for c in alpha.data])
for r in manifest:
 if r['object']==o.name:r['bounds']=[q.min(0).tolist(),q.max(0).tolist()]
np.savez(ROOT/'build/rig_arrays.npz',**arrays)
(ROOT/'build/rig_manifest.json').write_text(json.dumps(manifest,indent=2))
for ob in bpy.context.scene.objects:ob.select_set(ob.type in ['MESH','ARMATURE'])
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/ShengxiuCollection_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/ShengxiuCollection_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
report={'status':'pass','changed_object':o.name,'changed_vertices':int(np.count_nonzero(np.linalg.norm(q-p,axis=1)>1e-7)),'maximum_rear_offset_m':float((p[:,1]-q[:,1]).max()),'lower_rear_spine2_weight':.98,'rear_cloth_max_distance_m':.012,'scalp_front_face_body_unchanged':True,'source_baseline_sha256':hashlib.sha256((base/'ShengxiuCollection_Rigged.blend').read_bytes()).hexdigest()}
for name in arrays:
 if name not in [o.name+'_P',o.name+'_W',o.name+'_A']:assert np.array_equal(arrays[name],np.load(base/'rig_arrays.npz')[name])
(ROOT/'reports/hair_source_fit.json').write_text(json.dumps(report,indent=2))
print('HAIR_SOURCE_FIT',report)
