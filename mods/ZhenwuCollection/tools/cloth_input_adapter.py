"""Solver-only adapter for explicit duplicated front/back garment surfaces.
Runtime vertices, normals, triangles, Alpha and skin remain untouched.
"""
import copy,numpy as np

def adapt_mesh(mesh):
 result=copy.deepcopy(mesh);p=np.asarray(mesh['positions']);a=mesh['alpha'];w=mesh['weights'];b=mesh['bones'];n=np.asarray(mesh['normals'],float).copy()
 keys={};groups=[];mapping=[]
 for i,co in enumerate(p):
  key=(tuple(co),int(a[i]),tuple(w[i]),tuple(b[i]))
  if key not in keys:keys[key]=len(groups);groups.append([])
  k=keys[key];groups[k].append(i);mapping.append(k)
 fixes=[]
 for ids in groups:
  if np.linalg.norm(n[ids].sum(0))<1e-5:
   seed=n[ids[0]].copy();seed/=np.linalg.norm(seed);n[ids]=seed
   fixes.append({'render_vertices':ids,'solver_normal':seed.tolist(),'reason':'Coincident opposing front/back normals cancel; canonical source orientation used only for simulation.'})
 faces=np.asarray(mesh['indices'],int).reshape(-1,3);mapping=np.asarray(mapping);seen=set();retained=[];duplicates=0;degenerate=0
 for tri in faces:
  key=tuple(sorted(mapping[tri].tolist()))
  if len(set(key))<3:degenerate+=1;continue
  if key in seen:duplicates+=1;continue
  seen.add(key);retained.append(tri)
 result['normals']=n.tolist();result['indices']=np.asarray(retained,int).ravel().tolist()
 return result,{'normal_cancellation_groups':fixes,'duplicate_solver_faces_removed':duplicates,'degenerate_solver_faces_removed':degenerate,'runtime_geometry_changed':False,'simulation_faces':len(retained),'source_faces':len(faces)}
