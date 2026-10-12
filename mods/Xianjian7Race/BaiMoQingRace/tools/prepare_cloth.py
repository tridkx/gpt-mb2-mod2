"""Paint explicit measured hanging components; fitted clothing remains skeletal."""
from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));data=np.load(R/'build/fitted_model.npz');alphas={};rows=[]
for rec in json.loads((R/'build/manifest.json').read_text()):
 name=rec['object'];p=data[name+'_p'];q,owner=np.unique(np.round(p,6),axis=0,return_inverse=True);f=owner[data[name+'_f']];edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);count,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(q),len(q))),directed=False)
 a=np.zeros(len(p));selected=[]
 for component in range(count):
  ids=np.flatnonzero(labels[owner]==component);part=p[ids];lo=part.min(0);hi=part.max(0);height=hi[2]-lo[2]
  for rule in cfg['cloth_rules']:
   if rec['material']!=rule['material'] or height<rule['min_height_m'] or not rule['top_range_m'][0]<=hi[2]<=rule['top_range_m'][1] or not rule['bottom_range_m'][0]<=lo[2]<=rule['bottom_range_m'][1]:continue
   root=hi[2]-rule['root_band_m'];distance=np.maximum(root-part[:,2],0);travel=np.minimum(distance*rule['travel_slope'],rule['max_travel_m']);travel[travel<.008]=0;a[ids]=travel
   selected.append(dict(component=component,kind=rule['kind'],bounds_m=[lo.tolist(),hi.tolist()],root_height_m=float(root),fixed_vertices=int((travel==0).sum()),active_vertices=int((travel>0).sum())))
   assert (travel==0).any();break
 alphas[name]=a.astype('f4');rows.append(dict(object=name,material=rec['material'],components=selected,active_vertices=int((a>0).sum()),max_travel_m=float(a.max())))
np.savez_compressed(R/'build/cloth_alphas.npz',**alphas)
(R/'reports/cloth_paint.json').write_text(json.dumps(dict(scope='Explicit model-specific material, component extent and upper attachment rules',rows=rows),indent=2))
print('CLOTH_PAINTED',[(r['material'],len(r['components']),r['active_vertices']) for r in rows if r['active_vertices']])
