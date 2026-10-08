"""Reopen Blend and FBX and compare source geometry to the final runtime package."""
from pathlib import Path
import bpy,json,numpy as np
ROOT=Path(__file__).resolve().parents[1];data={m['name']:m for m in json.loads((ROOT/'build/no_cloth/final.json').read_text()) if m['lod']==0}
checks=[]
for kind in ['blend','fbx']:
 if kind=='blend':bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangT5_Rigged.blend'))
 else:
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(ROOT/'source/TianxiangT5_Rigged.fbx'))
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==14
 arm=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];assert len(arm)==1 and len(arm[0].data.bones)==28
 errors={}
 for o in objects:
  p=np.array(data[o.name]['pos']);s=np.array([o.matrix_world@v.co for v in o.data.vertices]);dist=np.array([np.linalg.norm(p-v,axis=1).min() for v in s]);assert dist.max()<3e-6,(kind,o.name,dist.max());errors[o.name]=float(dist.max())
  assert all(v.groups for v in o.data.vertices);assert not any(m.type=='CLOTH' for m in o.modifiers)
 if kind=='blend':
  images=[i for i in bpy.data.images if i.source=='FILE'];assert all(i.packed_file for i in images)
  assert all(i.filepath.replace('\\','/').startswith('//../tex/') for i in images),[(i.name,i.filepath) for i in images]
  thigh=bpy.data.objects['tx5_legs_06'];tex=[n.image for n in thigh.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE'];assert tex and all(Path(i.filepath.replace('\\','/')).name=='body_D.png' for i in tex)
  a=bpy.data.objects['tx5_body_04'];b=bpy.data.objects['tx5_head_11'];shared=set(tuple(round(x,6) for x in v.co) for v in a.data.vertices)&set(tuple(round(x,6) for x in v.co) for v in b.data.vertices);assert len(shared)==18
 checks.append({'format':kind,'mesh_count':14,'bones':28,'position_errors_m':errors,'skinning_retained':True,'cloth_modifiers':0})
(ROOT/'reports/appearance_source_validation.json').write_text(json.dumps({'status':'pass','checks':checks},indent=2));print('SOURCE_CHECK_PASS')

