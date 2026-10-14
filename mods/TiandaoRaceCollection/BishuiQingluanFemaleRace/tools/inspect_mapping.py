import sys,json
import numpy as np
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(workspace_root(R)/'tools/cloth_compiler'))
from mapping_payload import read
plans=json.loads((R/'build/mapped_render_maps/manifest.json').read_text());inputs={json.loads(p.read_text())['guid']:json.loads(p.read_text()) for p in (R/'build/cloth_final').glob('*.mesh.json')};source=np.load(R/'build/fitted_model.npz')
for plan in plans:
 m=inputs[plan['guid']];i,w=read(Path(plan['path']).read_bytes());active=np.array(m['alpha'])>0;active[plan['unmapped_vertices']]=False;v=np.maximum(-w[:,:3],0).max(1);ids=np.flatnonzero(active&(v>.3))
 print(m['name'],'extrap',v[active].max(),'outliers',len(ids))
 for k in ids[np.argsort(-v[ids])[:5]]:print(k,np.array(m['positions'])[k].round(4),w[k], 'skirt', k in plan['skirt_vertices'])
