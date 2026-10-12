"""Measure this source's anatomy and skirt connected components in metres."""
import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
arrays={};rows=[]
for o in sorted(bpy.data.objects,key=lambda o:o.name):
    if o.type!='MESH':continue
    p=np.array([o.matrix_world@v.co for v in o.data.vertices])*.01
    o.data.calc_loop_triangles();f=np.array([list(t.vertices) for t in o.data.loop_triangles])
    arrays[o.name+'_p']=p;arrays[o.name+'_f']=f
    for x in [.075,.106,.12,.245,.374,.396,.425]:
        q=p[(abs(abs(p[:,0])-x)<.009)&(p[:,0]>0)]
        if len(q)>4:rows.append({'mesh':o.name,'x':x,'n':len(q),'median':np.median(q,axis=0).tolist(),'z_range':[float(q[:,2].min()),float(q[:,2].max())]})
    if o.name==json.loads((R/'tools/model_config.json').read_text())['skirt_source']:
        parent=list(range(len(p)))
        def root(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for e in o.data.edges:a,b=e.vertices;parent[root(a)]=root(b)
        groups={}
        for i in range(len(p)):groups.setdefault(root(i),[]).append(i)
        components=[]
        for ids in groups.values():
            q=p[ids];components.append({'vertices':len(ids),'bbox':[q.min(0).tolist(),q.max(0).tolist()]})
        (R/'reports/skirt_components.json').write_text(json.dumps(components,indent=2))
np.savez_compressed(R/'build/source_samples.npz',**arrays)
(R/'reports/anatomy_sections.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
