import bpy,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1].as_posix()
bpy.ops.wm.open_mainfile(filepath=ROOT+'/source/inspection.blend')
report={}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 n=len(o.data.vertices); par=list(range(n))
 def root(i):
  while par[i]!=i:par[i]=par[par[i]];i=par[i]
  return i
 for e in o.data.edges:
  a,b=e.vertices;par[root(a)]=root(b)
 comps={}
 for v in o.data.vertices:comps.setdefault(root(v.index),[]).append(o.matrix_world@v.co)
 report[o.name]=[{'n':len(p),'bounds':[[round(min(v[i] for v in p)*.01,4),round(max(v[i] for v in p)*.01,4)] for i in range(3)]} for p in sorted(comps.values(),key=len,reverse=True) if len(p)>8]
open(ROOT+'/reports/components.json','w').write(json.dumps(report,indent=1))
