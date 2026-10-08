"""Calibrate skirt anchor following against native motions; proxy diagnostics."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,pose,skin_matrices,lbs
a=np.load(ROOT/'build/rig_arrays.npz');p=a['rq1_body_12_P'];w=a['rq1_body_12_W']
# Rest positions stay fixed during this estimate. The selected setting must
# subsequently rebuild/recheck the package, rather than treat this as final QA.
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
samples=[]
for label in ['run','riding']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
    for f in range(max(1,anim['start']),anim['frames']):samples.append((label,f,pose(rig,anim,f)[:,:3,3],skin_matrices(rig,anim,f)))
results=[];legids=[1,2,5,6];waistids=[0,9,10];old=w[:,legids].sum(1)
for follow in [.6,.7,.8,.9,1.0]:
    candidate=w.copy();total=np.clip(old*follow/.6,0,1)
    candidate[:,legids]*=follow/.6
    candidate[:,waistids]*=((1-total)/np.maximum(1-old,1e-9))[:,None]
    keep=np.argsort(-candidate,axis=1)[:,:4];bw=np.take_along_axis(candidate,keep,axis=1)*255
    maximum=0;bylabel={}
    for label,f,joints,skin in samples:
        points=lbs(p,keep,bw,skin);gap=[]
        for start,end,radius in [(1,2,.075),(2,3,.050),(5,6,.075),(6,7,.050)]:
            pos=joints[start];axis=joints[end]-pos;t=np.clip((points-pos)@axis/(axis@axis),0,1)
            gap.append(np.linalg.norm(points-pos-t[:,None]*axis,axis=1)-radius)
        depth=max(0,-float(np.min(gap)));maximum=max(maximum,depth);bylabel[label]=max(bylabel.get(label,0),depth)
    results.append({'follow':follow,'max_vertex_proxy_overlap_m':maximum,'motions':bylabel})
(ROOT/'reports/skirt_calibration.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
