"""Paint model-specific travel distances without changing accepted geometry."""
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

R=Path(__file__).resolve().parents[1]
data=np.load(R/'build/fitted_model.npz');alphas={};rows=[]
rig=json.loads((R/'reports/weight_transfer.json').read_text())
names=rig['native_bones'];joints=np.array(rig['source_landmarks'])

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

for rec in json.loads((R/'build/manifest.json').read_text()):
    name=rec['object'];p=data[name+'_p'];faces=data[name+'_f'];a=np.zeros(len(p))
    q,owner=np.unique(p,axis=0,return_inverse=True);f=owner[faces]
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    count,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(q),len(q))),directed=False)
    label=labels[owner];selected=[]
    if name=='yqs_part_03':
        # The hanging sleeve panels sit behind the fitted sleeves; the torso,
        # shoulder seam, arm tube and cuffs remain attached to the skeleton.
        distance=np.full(len(p),100.)
        for pre in ['l','r']:
            chain=[joints[names.index(pre+'_'+n)] for n in ['upperarm_twist','foretwist','hand']]
            for start,end in zip(chain[:-1],chain[1:]):
                axis=end-start;t=np.clip((p-start)@axis/(axis@axis),0,1)
                distance=np.minimum(distance,np.linalg.norm(p-start-t[:,None]*axis,axis=1))
        a=np.clip(distance-.075,0,.30)*smooth(.10,.16,np.abs(p[:,0]))*(1-smooth(-.005,.025,p[:,1]))
        a[a<.006]=0
    else:
        for component in range(count):
            ids=np.flatnonzero(label==component);part=p[ids];lo=part.min(0);hi=part.max(0);height=hi[2]-lo[2]
            kind=None
            if name=='yqs_part_00' and height>.12 and lo[2]<1.44:
                kind='long_hair';distance=np.maximum(hi[2]-.025-part[:,2],0);travel=np.minimum(distance*.70,.38)
            elif name=='yqs_part_10' and lo[2]>.60 and hi[2]<1.18 and height>.14:
                kind='skirt';distance=np.maximum(hi[2]-.025-part[:,2],0);travel=np.minimum(distance*.85,.34)
            elif name=='yqs_part_10' and lo[2]>.80 and hi[2]>1.50 and height>.30:
                kind='hair_ribbon';distance=np.maximum(hi[2]-.025-part[:,2],0);travel=np.minimum(distance*.70,.34)
            elif name=='yqs_part_11' and height>.025:
                kind='tassel';distance=np.maximum(hi[2]-.008-part[:,2],0);travel=np.minimum(distance*.65,.055)
            if kind:
                travel[travel<.006]=0;a[ids]=travel
                selected.append(dict(component=component,kind=kind,vertices=len(ids),bounds=[lo.tolist(),hi.tolist()]))
    alphas[name]=a.astype('f4')
    rows.append(dict(object=name,active_vertices=int((a>0).sum()),fixed_vertices=int((a==0).sum()),max_travel_m=float(a.max()),components=selected))
np.savez_compressed(R/'build/cloth_alphas.npz',**alphas)
(R/'reports/cloth_paint.json').write_text(json.dumps(rows,indent=2))
print('CLOTH_PAINT',[(r['object'],r['active_vertices'],round(r['max_travel_m'],3)) for r in rows])
