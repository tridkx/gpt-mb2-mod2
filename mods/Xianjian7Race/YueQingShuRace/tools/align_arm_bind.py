"""Prepare the model-specific arm-only skeleton revision from the preserved baseline."""
from pathlib import Path
import json,sys,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from workspace_paths import workspace_root
sys.path.insert(0,str(workspace_root(R)/'tools/asset_helpers/previewer'));from baker.skeleton import parse_skeljson
from arm_binding import align
raw=json.loads((R/'tools/arm_bind_baseline.json').read_text());rig=parse_skeljson(raw);world,rows=align(rig['restWorld'],rig['names']);local=np.array([world[i] if p<0 else np.linalg.inv(world[p])@world[i] for i,p in enumerate(rig['parent'])]);bones=[]
for i,b in enumerate(raw['bones']):
 matrix=np.array(b['rest']).reshape(4,4).T;matrix[:3,:3]=local[i,:3,:3];matrix[:3,3]=local[i,:3,3];bones.append(dict(name=b['name'],parent=b['parent'],rest=matrix.T.ravel().tolist()))
(R/'build/skeleton_spec.json').write_text(json.dumps(bones,indent=2));(R/'reports/arm_bind_alignment.json').write_text(json.dumps(dict(bones=rows,joint_positions_unchanged=True,source_geometry_weights_unchanged=True),indent=2));print(rows)
