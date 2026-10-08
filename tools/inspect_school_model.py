"""Measure an individual source model; no rig, UV or game edits."""
import bpy,sys,json
import numpy as np
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root/'input/model.fbx'),use_anim=False)
rows=[];arrays={}
for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
    if o.type!='MESH':continue
    p=np.array([o.matrix_world@v.co for v in o.data.vertices]);arrays[o.name]=p
    mat=o.data.materials[0];tex=next((n.image.name for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
    # Components isolate hands, neck and separate garment panels.
    parent=list(range(len(p)))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for e in o.data.edges:parent[find(e.vertices[1])]=find(e.vertices[0])
    groups={}
    for i in range(len(p)):groups.setdefault(find(i),[]).append(i)
    components=[{'vertices':len(v),'min':p[v].min(0).tolist(),'max':p[v].max(0).tolist(),'center':p[v].mean(0).tolist()} for v in groups.values() if len(v)>8]
    row={'name':o.name,'vertices':len(p),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'texture':tex,'min':p.min(0).tolist(),'max':p.max(0).tolist(),'components':components}
    rows.append(row)
np.savez_compressed(root/'build/source_measured.npz',**arrays)
report={'armatures':len([o for o in bpy.context.scene.objects if o.type=='ARMATURE']),'meshes':rows}
(root/'reports/source_inspection.json').write_text(json.dumps(report,indent=2))
print('SOURCE_INSPECTED',report['armatures'],'armatures',len(rows),'meshes')
for m in rows:print(m['name'],m['texture'],m['vertices'],np.round(m['min'],2).tolist(),np.round(m['max'],2).tolist())
