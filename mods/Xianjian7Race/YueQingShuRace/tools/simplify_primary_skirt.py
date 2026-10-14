"""Simplify the main source skirt surface without replacing the render mesh."""
from pathlib import Path
import json
import bpy
import numpy as np

R = Path(__file__).resolve().parents[1]
d = np.load(R/'build/fitted_model.npz')
p = d['yqs_part_10_p']; q,inv=np.unique(p,axis=0,return_inverse=True)
f=inv[d['yqs_part_10_f']]
e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
parent=np.arange(len(q))
def find(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]];i=parent[i]
    return i
for a,b in e:
    a,b=find(a),find(b)
    if a!=b: parent[max(a,b)]=min(a,b)
roots=np.array([find(i) for i in range(len(q))])
_,labels=np.unique(roots,return_inverse=True)
paint=json.loads((R/'reports/cloth_paint.json').read_text())
row=next(x for x in paint if x['object']=='yqs_part_10')
parts=[x['component'] for x in row['components'] if x['kind']=='skirt']
component=max(parts,key=lambda c:int((labels==c).sum()))
ids=np.flatnonzero(labels==component); owner=np.full(len(q),-1,int); owner[ids]=np.arange(len(ids))
faces=owner[f[(labels[f]==component).all(1)]]
# Drop duplicate faces if source front/back surfaces share the same positions.
_,unique=np.unique(np.sort(faces,axis=1),axis=0,return_index=True); faces=faces[unique]
mesh=bpy.data.meshes.new('SkirtSimulation');mesh.from_pydata(q[ids].tolist(),[],faces.tolist());mesh.update()
obj=bpy.data.objects.new('SkirtSimulation',mesh);bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
mod=obj.modifiers.new('SimplifySimulationOnly','DECIMATE');mod.ratio=.45;mod.use_collapse_triangulate=True
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
mesh.calc_loop_triangles()
result=dict(positions=[list(v.co) for v in mesh.vertices],indices=[list(t.vertices) for t in mesh.loop_triangles],source_component=component,source_vertices=len(ids),ratio=.45)
(R/'build/simplified_primary_skirt.json').write_text(json.dumps(result))
print('SIMPLIFIED_MAIN_SKIRT',len(ids),len(mesh.vertices),len(mesh.loop_triangles))
