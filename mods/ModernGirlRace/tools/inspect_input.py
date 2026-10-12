import bpy, json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
rows=[]
for o in sorted(bpy.data.objects,key=lambda x:x.name):
    if o.type!='MESH':continue
    p=np.array([o.matrix_world@v.co for v in o.data.vertices])
    rows.append(dict(name=o.name,vertices=len(p),bbox=[p.min(0).tolist(),p.max(0).tolist()],images=[n.image.filepath for m in o.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]))
(R/'reports/source_measurements.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
