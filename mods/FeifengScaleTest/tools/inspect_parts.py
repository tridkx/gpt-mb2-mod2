import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
p=np.array([o.matrix_world@v.co for v in o.data.vertices])
rows=[]
for i,m in enumerate(o.data.materials):
 ids=sorted({vi for f in o.data.polygons if f.material_index==i for vi in f.vertices})
 rows.append(dict(slot=i,material=m.name,images=[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],vertices=len(ids),bounds=[p[ids].min(0).tolist(),p[ids].max(0).tolist()]))
(R/'reports/material_inspection.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
