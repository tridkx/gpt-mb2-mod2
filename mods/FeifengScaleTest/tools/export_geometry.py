import bpy,json,sys
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/pipeline'))
from build_assets import vertex_tangents
bpy.ops.wm.open_mainfile(filepath=str(R/'source/Feifeng_Test_Rigged.blend'))
(R/'build/mesh').mkdir(exist_ok=True);rows=[]
for rec in json.loads((R/'build/rig_manifest.json').read_text()):
 ob=bpy.data.objects[rec['object']];me=ob.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;records=[];faces=[];dedup={}
 for tri in me.loop_triangles:
  face=[]
  for li in tri.loops:
   vi=me.loops[li].vertex_index;v=me.vertices[vi];normal=me.corner_normals[li].vector.normalized();u=list(uv[li].uv);u[1]=1-u[1];key=(vi,tuple(normal),tuple(u))
   if key not in dedup:
    influences=sorted([(int(ob.vertex_groups[g.group].name.rsplit('_',1)[1]),g.weight) for g in v.groups if g.weight>0],key=lambda row:-row[1])[:4]
    ids=[i for i,w in influences];w=np.array([w for i,w in influences]);w/=w.sum();q=np.rint(w*255).astype(int);q[w.argmax()]+=255-q.sum()
    while len(ids)<4:ids.append(0);q=np.append(q,0)
    dedup[key]=len(records);records.append((list(v.co),list(normal),u,ids,q.tolist()))
   face.append(dedup[key])
  faces.append(face)
 p=np.array([v[0] for v in records]);normal=np.array([v[1] for v in records]);uvs=np.array([v[2] for v in records]);f=np.array(faces);tangent=vertex_tangents(p,f,uvs,normal)
 assert np.isfinite(p).all() and np.isfinite(tangent).all()
 # Identical small test geometry at each LOD isolates skeleton behavior.
 for lod in range(4):
  name=rec['object']+('' if lod==0 else '.lod'+str(lod));path=R/'build/mesh'/(name+'.mgeo')
  with path.open('wb') as out:
   out.write(np.array([0x4f45474d,len(p),f.size],'<i4').tobytes())
   for a in [p,normal,tangent,uvs,np.zeros((len(p),2))]:out.write(np.asarray(a,'<f4').tobytes())
   for a in [np.full((len(p),4),255),[r[3] for r in records],[r[4] for r in records]]:out.write(np.asarray(a,'u1').tobytes())
   out.write(f.astype('<u4').tobytes())
  rows.append(dict(profile=rec['profile'],part=rec['part'],name=name,geometry=str(path),material=rec['material'],flags=[],materialFlags=['no_team_color','no_tattoo'],lod=lod,vertices=len(p),triangles=len(f)))
(R/'build/geometry.json').write_text(json.dumps(rows,indent=2));print('GEOMETRY_READY',len(rows))
