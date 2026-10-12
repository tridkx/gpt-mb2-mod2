"""Read source anatomy, texture nodes, material parts and connected components."""
import bpy,json,sys
import numpy as np
from pathlib import Path
R=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else Path(__file__).resolve().parents[1]
cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(R/cfg['source_blend']))
ob=next(o for o in bpy.data.objects if o.type=='MESH');arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
me=ob.data;me.calc_loop_triangles();C=np.diag([-1.,-1.,1.]);p=np.array([ob.matrix_world@v.co for v in me.vertices])@C
parts=[]
for i,s in enumerate(ob.material_slots):
 ids=sorted({v for f in me.polygons if f.material_index==i for v in f.vertices})
 if not ids:continue
 q=p[ids];nodes=s.material.node_tree.nodes
 parts.append(dict(index=i,material=s.material.name,vertices=len(ids),triangles=sum(t.material_index==i for t in me.loop_triangles),min=q.min(0).tolist(),max=q.max(0).tolist(),images=[dict(name=n.image.name,path=n.image.filepath) for n in nodes if n.type=='TEX_IMAGE' and n.image]))
report=dict(height_m=float(np.ptp(p[:,2])),parts=parts,bones={b.name:dict(head=(np.array(arm.matrix_world@b.head_local)@C).tolist(),tail=(np.array(arm.matrix_world@b.tail_local)@C).tolist(),parent=b.parent.name if b.parent else None) for b in arm.data.bones})
(R/'reports/input_inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('INSPECTED',R.name,report['height_m'])
for x in parts:print(x['index'],x['material'],x['triangles'],x['min'],x['max'],[a['name'] for a in x['images']])
