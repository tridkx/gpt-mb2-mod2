"""Read source FBX coordinates, topology, materials and any existing rig."""
import bpy, json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
rows=[]; arrays={}
for o in sorted(bpy.data.objects,key=lambda x:x.name):
    if o.type!='MESH':continue
    p=np.array([o.matrix_world@v.co for v in o.data.vertices]);o.data.calc_loop_triangles()
    arrays[o.name+'_p']=p
    arrays[o.name+'_f']=np.array([list(t.vertices) for t in o.data.loop_triangles],dtype='i4')
    rows.append(dict(name=o.name,vertices=len(p),triangles=len(o.data.loop_triangles),bbox_world=[p.min(0).tolist(),p.max(0).tolist()],groups=[g.name for g in o.vertex_groups],materials=[m.name for m in o.data.materials],uv_layers=[u.name for u in o.data.uv_layers]))
arms=[dict(name=o.name,bones=[dict(name=b.name,head=list(o.matrix_world@b.head_local),tail=list(o.matrix_world@b.tail_local)) for b in o.data.bones]) for o in bpy.data.objects if o.type=='ARMATURE']
result=dict(meshes=rows,armatures=arms,scene_scale=bpy.context.scene.unit_settings.scale_length)
(R/'reports/source_measurements.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
np.savez_compressed(R/'build/source_arrays.npz',**arrays)
print(json.dumps(result,indent=2))
