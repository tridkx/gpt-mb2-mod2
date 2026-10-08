import bpy,sys,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project_paths import resolve_project
ROOT=resolve_project(Path(__file__).resolve().parents[1],sys.argv[sys.argv.index('--')+1]);BASE=ROOT/'build/repair_baseline_v1.0.0'
bpy.ops.wm.open_mainfile(filepath=str(BASE/f'source/{ROOT.name}_Rigged.blend'))
r=json.loads((BASE/'rig_manifest.json').read_text());o=bpy.data.objects[next(r['object'] for r in r if r['kind']=='skirt')]
parent=list(range(len(o.data.vertices)))
def find(v):
    while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
    return v
for e in o.data.edges:parent[find(e.vertices[1])]=find(e.vertices[0])
groups={}
for vi in range(len(parent)):groups.setdefault(find(vi),[]).append(vi)
(ROOT/'build/skirt_panels.json').write_text(json.dumps(list(groups.values())));print('SKIRT_PANELS',len(groups))
o.data.calc_loop_triangles()
(ROOT/'build/skirt_triangles.json').write_text(json.dumps([list(t.vertices) for t in o.data.loop_triangles]))
