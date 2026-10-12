"""Cook Pal7 two-sided cards with an explicit cancelled-normal fallback."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(workspace_root(R)/'tools/cloth_compiler'))
from cook_cloth import cook
policy=json.loads((R/'tools/cloth_policy.json').read_text());out=R/'build/cooked_cloth';out.mkdir(exist_ok=True);plans=[];fallbacks=[]
for path in sorted((R/'build/cloth_inputs').glob('*.mesh.json')):
 mesh=json.loads(path.read_text());p=np.array(mesh['positions']);n=np.array(mesh['normals']);keys=np.column_stack([p,np.array(mesh['alpha']),np.array(mesh['weights']),np.array(mesh['bones'])]);unique,mapping=np.unique(keys,axis=0,return_inverse=True)
 sums=np.zeros((len(unique),3));np.add.at(sums,mapping,n);cancelled=np.flatnonzero(np.linalg.norm(sums,axis=1)<1e-5)
 for index in cancelled:
  ids=np.flatnonzero(mapping==index);valid=ids[np.linalg.norm(n[ids],axis=1)>.5];assert len(valid)
  # Preserve rendering normals. Only a solver normal at coincident opposite
  # card faces uses one of the existing source normals instead of zero.
  n[ids]=n[valid[0]]
 if len(cancelled):
  mesh['normals']=n.tolist();fallbacks.append(dict(mesh=mesh['name'],cancelled_positions=len(cancelled),source_mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),solver_only=True,render_normals_unchanged=True))
 raw,row=cook(mesh,policy['meshes'].get(mesh['name'],policy['default']));dest=out/(row['guid']+'.bin');dest.write_bytes(raw);row['path']=str(dest.resolve());plans.append(row)
 print('COOKED',mesh['name'],len(raw),flush=True)
(out/'manifest.json').write_text(json.dumps(plans,indent=2))
(R/'reports/cloth_normal_fallback.json').write_text(json.dumps(dict(scope='Coincident source card normals that sum to zero; deterministic existing-normal solver fallback',rows=fallbacks),indent=2))
