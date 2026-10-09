import bpy,json,sys
import numpy as np
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root/'input/model.fbx'),use_anim=False)
rows=[]
for o in sorted(bpy.context.scene.objects,key=lambda x:x.name):
    if o.type!='MESH':continue
    slots=[]
    for mat in o.data.materials:
        if not mat:continue
        bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        color=bs.inputs['Base Color'].links[0].from_node if bs and bs.inputs['Base Color'].is_linked else None
        slots.append({'name':mat.name,'diffuse':color.image.filepath if color and color.type=='TEX_IMAGE' else None,'images':[{ 'name':n.image.name,'path':n.image.filepath } for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
    rows.append({'name':o.name,'slots':slots,'face_slots':sorted(set(f.material_index for f in o.data.polygons))})
(root/'reports/material_inspection.json').write_text(json.dumps(rows,indent=2))
print('MATERIALS_INSPECTED',len(rows))
