"""Scan shoulder/elbow/wrist locations across full Native inventory candidate cycles."""
from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent));from workspace_paths import workspace_root
sys.path.insert(0,str(workspace_root(R)/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));rows=[]
for label in ['idle','ui_neutral_female']:
 anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()));frames=range(max(1,anim['start']),anim['frames']);values=[];joints=[]
 for frame in frames:
  skin=skin_matrices(rig,anim,frame);world=skin@rig['restWorld'];pelvis=world[rig['names'].index('pelvis'),:3,3];forward=skin[rig['names'].index('pelvis'),:3,:3]@np.array([0.,1.,0.]);forward/=np.linalg.norm(forward)
  points=np.array([world[rig['names'].index(n),:3,3] for n in ['l_upperarm_twist','l_foretwist','l_hand','r_upperarm_twist','r_foretwist','r_hand']]);joints.append(points);values.append((points[[2,5]]-pelvis)@forward)
 values=np.array(values);joints=np.array(joints);worst=int(np.argmin(values.min(1)));rows.append(dict(label=label,asset=anim['name'] if 'name' in anim else json.loads((R/'reports'/(label+'.json')).read_text())['name'],frames_checked=len(frames),wrist_forward_of_pelvis_range_m=[float(values.min()),float(values.max())],worst_frame=list(frames)[worst],wrist_world_y_bounds_m=[float(joints[:,[2,5],1].min()),float(joints[:,[2,5],1].max())],shoulder_elbow_wrist_bounds_m=[joints.min((0,1)).tolist(),joints.max((0,1)).tolist()]))
report=dict(status='pass',version=json.loads((R/'tools/model_config.json').read_text())['version'],rows=rows,scope='Every decoded non-bind frame; posed skeletal shoulder/elbow/wrist positions, not engine cloth or proof of all intersections',game_verified=False)
assert np.isfinite(joints).all()
assert rows[1]['wrist_world_y_bounds_m'][0]>rows[0]['wrist_world_y_bounds_m'][0],rows
(R/'reports/inventory_pose_validation.json').write_text(json.dumps(report,indent=2));print(rows)
