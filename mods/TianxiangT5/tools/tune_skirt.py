"""Compare candidate skirt anchors against moving leg capsules, offline only."""
from pathlib import Path
import json,sys,itertools
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices
from motion_fit import skirt_weights,skirt_clearance

a=np.load(ROOT/'build/movement_baseline/rig_arrays.npz')
p=a['tx5_body_03_P'];source=a['tx5_body_03_S'];old=a['tx5_body_03_W']
core=old.copy();core[:,[1,5]]=0
core/=np.maximum(core.sum(1,keepdims=True),1e-12)
rig=parse_skeljson(json.load(open(ROOT/'reports/human_skeleton.json')))
anim=parse_animjson(json.load(open(ROOT/'reports/run.json')))
skins=[skin_matrices(rig,anim,f) for f in range(max(1,anim['start']),anim['frames'])]
rest=rig['restWorld'][:,:3,3]

def skin(p,w,s):
    h=np.column_stack([p,np.ones(len(p))])
    return sum(w[:,i,None]*(h@s[i].T)[:,:3] for i in np.flatnonzero(w.sum(0)>0))

capsules=[]
for s in skins:
    segments=[]
    for bone,end,radius in [(1,2,.057),(2,3,.040),(3,4,.055),(5,6,.057),(6,7,.040),(7,8,.055)]:
        # Segment ends move with their actual owner bones.
        first=(s[bone]@np.r_[rest[bone],1])[:3]
        last=(s[end]@np.r_[rest[end],1])[:3]
        segments.append((first,last,radius))
    capsules.append(segments)

def score(p,w):
    chosen=source[:,2]<.93
    total=0.;worst=0.;contacts=0
    for s,segments in zip(skins,capsules):
        moved=skin(p,w,s)[chosen]
        gap=np.full(len(moved),np.inf)
        for first,last,radius in segments:
            axis=last-first
            t=np.clip((moved-first)@axis/(axis@axis),0,1)
            gap=np.minimum(gap,np.linalg.norm(moved-first-t[:,None]*axis,axis=1)-radius)
        depth=np.maximum(-gap,0)
        total+=float(depth.sum());worst=max(worst,float(depth.max()));contacts+=int((depth>.001).sum())
    return {'depth_sum_mm':total*1000,'max_depth_mm':worst*1000,'samples_over_1mm':contacts}

rows=[]
for front,back,calf,sagittal,waist_full in itertools.product([1.0],[.80,.95,1.0],[.55,.75,.90,1.0],[.040],[.86]):
    params=dict(front=front,back=back,calf=calf,sagittal=sagittal,waist_full=waist_full)
    row={'parameters':params,'score':score(skirt_clearance(p,source,sagittal=sagittal),skirt_weights(source,core,front,back,calf,waist_full))}
    rows.append(row)
rows.sort(key=lambda r:r['score']['depth_sum_mm'])
report={'proxy':'Offline thigh, calf and foot capsules; no game cloth solver','frames':len(skins),
        'baseline':score(p,old),'best_candidates':rows[:12]}
(ROOT/'reports/skirt_tuning.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
