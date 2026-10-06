import bpy, numpy as np, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/inspection.blend'))
objects=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name)
arrays={}
for i,o in enumerate(objects):
    p=np.array([o.matrix_world@v.co for v in o.data.vertices])*.01
    arrays[str(i)]=p
    if i not in {0,4,11}:continue
    # UV splits are welded for boundary analysis, without modifying the source.
    unique,inverse=np.unique(np.round(p,5),axis=0,return_inverse=True)
    edges={}
    for face in o.data.polygons:
        vv=[int(inverse[v]) for v in face.vertices]
        for a,b in zip(vv,vv[1:]+vv[:1]):
            edge=tuple(sorted((a,b)));edges[edge]=edges.get(edge,0)+1
    boundary=sorted({v for e,count in edges.items() if count==1 for v in e})
    neck=[v for v in boundary if abs(unique[v,0])<.09 and unique[v,2]>1.38]
    print('NECK_BOUNDARY',i,len(neck),unique[neck].round(5).tolist())
np.savez_compressed(ROOT/'build/original_arrays.npz',**arrays)
