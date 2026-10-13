"""Screen local pelvis coverage in Native poses; never claim engine simulation."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from workspace_paths import workspace_root
from pelvis_support import clearance,pose_capsule
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(workspace_root(R)/'tools/asset_helpers/previewer'))
from baker.animation import parse_animjson,skin_matrices,lbs
from baker.skeleton import parse_skeljson
data=np.load(R/'build/fitted_model.npz');p=data['yqs_part_08_p'];w=data['yqs_part_08_w'];f=data['yqs_part_08_f']
keep=(abs(p[:,0])<.2)&(p[:,2]>.82)&(p[:,2]<1.06);f=f[keep[f].all(1)]
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
bi=np.argsort(-w,axis=1)[:,:4];bw=np.floor(np.take_along_axis(w,bi,axis=1)*255).astype(int);bw[:,0]+=255-bw.sum(1)
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules'];rows=[]
for label in ['idle','run','bow','riding','slash']:
    anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()));frames=sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,12).astype(int)))
    maximum=0.;outside=0;count=0
    for frame in frames:
        skin=skin_matrices(rig,anim,frame);tri=lbs(p,bi,bw,skin)[f]
        points=np.concatenate([tri[:,0]*(i/4)+tri[:,1]*(j/4)+tri[:,2]*(1-(i+j)/4) for i in range(5) for j in range(5-i)])
        posed=[]
        for c in caps:
            ab=pose_capsule(c,skin,rig['names'])
            posed.append(dict(c,endpoints_m=np.array(ab).tolist()))
        gap=clearance(points,posed);maximum=max(maximum,float(gap.max()));outside+=int((gap>1e-7).sum());count+=len(gap)
    rows.append(dict(pose=label,sampled_frames=len(frames),samples=count,uncovered_samples=outside,maximum_outside_m=maximum))
report=dict(status='pass' if all(x['uncovered_samples']==0 for x in rows) else 'fail',rows=rows,scope='12 Native non-bind frames per motion; protected hip below rigid waistband (Z < 1.06 m), triangle vertices, edges and interiors; not full continuous collision',game_verified=False)
(R/'reports/panel_motion_validation.json').write_text(json.dumps(report,indent=2));print(report)
assert report['status']=='pass'
