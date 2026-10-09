"""CPU PBD sanity check of final hair constraints, gravity and own capsules.

This is an approximation, not the Bannerlord solver or game acceptance.
Checks settled static native poses, not a time-varying animation sequence.
"""
import json,sys,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(WS/'tools'))
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from hair_shape_analysis import read_geo,rear_surface
from cloth_compiler.cloth_payload import read,decode_positions
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rawrig=json.loads((ROOT/'reports/human_skeleton.json').read_text());rig=parse_skeljson(rawrig)
names={b['name']:b['i'] for b in rawrig['bones']}
folder=ROOT/'build/back_hair_final_dump'
mesh=next(json.loads(p.read_text()) for p in folder.glob('*.mesh.json') if json.loads(p.read_text())['name']=='sx_mingyu_head_00')
d=read(folder/f"sx_mingyu_head_{mesh['guid']}.bin")
rest=decode_positions(d);mapping=d['render_to_sim'];n=len(rest);fixed=np.arange(n)<d['normal_start'];mov=(~fixed).astype(float)
constraints=d['constraints'];lengths=d['rest_lengths'];roots=d['anchors']>>16;limits=(d['anchors']&65535)*d['anchor_scale']
caps=next(b for b in ET.parse(ROOT/'module/ShengxiuCollection/ModuleData/cloth_bodies.xml').getroot() if b.get('name')=='sx_mingyu_back_collision').findall('./capsules/capsule')
geo=[m for f in (ROOT/'build/back_hair_final_export/geo').glob('*.bin') for m in read_geo(f)]
hair=next(m for m in geo if m['name']=='sx_mingyu_head_00')
arrays=np.load(ROOT/'build/rig_arrays.npz')
_,source_ids=cKDTree(arrays['sx_mingyu_head_00_P']).query(hair['pos'])
original=np.load(ROOT/'build/hair_shape_baseline_v1.1.4/rig_arrays.npz')['sx_mingyu_head_00_P'][source_ids]
posterior=(original[:,1]<-.025)&(original[:,2]<1.50)
faces=hair['idx'].reshape(-1,3);face_ids=faces[posterior[faces].all(1)]
def capsule_pose(skin):
 rows=[]
 for cap in caps:
  f=np.fromstring(cap.get('frame'),sep=',').reshape(4,4)
  ends=np.array([f[3,:3],f[3,:3]+f[0,:3]*float(cap.get('length'))])
  radius=[]
  for i,point in enumerate(cap.findall('./points/point')):
   v=ends[i].copy();ends[i]=sum((skin[names[b.get('name')],:3,:3]@v+skin[names[b.get('name')],:3,3])*float(b.get('weight')) for b in point.findall('./bones/bone'))
   radius.append(float(point.get('radius')))
  axis=ends[1]-ends[0];size=np.linalg.norm(axis);rows.append((ends[0],axis/size,size,*radius))
 return rows
def collide(p,rows):
 for c,u,size,r0,r1 in rows:
  t=np.clip((p-c)@u,0,size);center=c+t[:,None]*u
  delta=p-center;length=np.linalg.norm(delta,axis=1);radius=r0+(r1-r0)*t/size
  push=np.maximum(radius-length,0)/np.maximum(length,1e-12)
  p+=delta*(push*mov)[:,None]
 return p
def distance_clamp(p,target):
 delta=p-target;length=np.linalg.norm(delta,axis=1)
 p=target+delta*np.minimum(1,d['max_distances']/np.maximum(length,1e-12))[:,None]
 p[fixed]=target[fixed];return p
def surface_gaps(p,skin):
 tri=[]
 for m in geo:
  if m['name'] not in ['sx_mingyu_body_01','sx_mingyu_body_02','sx_mingyu_body_13','sx_mingyu_body_06']:continue
  vv=m['pos'][m['idx'].reshape(-1,3)];keep=(abs(vv[:,:,0]).max(1)<.18)&(vv[:,:,1].min(1)>-.18)&(vv[:,:,2].min(1)>.90)
  pp=lbs(m['pos'],m['bi'],m['bw'],skin);tri.append(pp[m['idx'].reshape(-1,3)][keep])
 tri=np.concatenate(tri)
 # Local torso coordinates maintain the same rear-ray definition for each pose.
 inv=np.linalg.inv(skin[11]);tri=(tri-skin[11,:3,3])@inv[:3,:3].T
 samples=np.concatenate([p[posterior],p[face_ids].mean(1),*(p[face_ids[:,[a,b]]].mean(1) for a,b in [(0,1),(1,2),(2,0)])])
 samples=(samples-skin[11,:3,3])@inv[:3,:3].T
 surf=rear_surface(samples,tri);valid=np.isfinite(surf);gap=surf[valid]-samples[valid,1]
 return dict(covered_samples=int(valid.sum()),inside_samples=int((gap<-.001).sum()),minimum_gap_m=float(gap.min()),median_gap_m=float(np.median(gap)),worst_sample_local=samples[valid][gap.argmin()].tolist())
rows=[];positions={}
for label,frame in [('rest',0),('idle',169),('idle',1000),('run',1),('run',13),('bow',75),('riding',10)]:
 skin=np.repeat(np.eye(4)[None],28,axis=0) if label=='rest' else skin_matrices(rig,parse_animjson(json.loads((ROOT/f'reports/{label}.json').read_text())),frame)
 target=lbs(rest,d['bone_indices'].reshape(-1,4),d['bone_weights'].reshape(-1,4)*255,skin)
 caprows=capsule_pose(skin);p=target.copy();prev=p.copy()
 initial_projection=collide(target.copy(),caprows)-target
 for step in range(360):
  oldp=p.copy();p=p+(p-prev)*np.sqrt(.48)+np.array([0,0,-7/120**2]);prev=oldp
  p=distance_clamp(p,target)
  for iteration in range(2):
   delta=p-p[roots];length=np.linalg.norm(delta,axis=1)
   p-=delta*np.maximum(0,1-limits/np.maximum(length,1e-12))[:,None]*mov[:,None]
   for s in d['constraint_sets']:
    for kind,stiffness in [(0,1),(2,.18)]:
     start,count=s[kind*2:kind*2+2];ids=np.arange(start,start+count);a,b=constraints[ids].T
     delta=p[b]-p[a];length=np.linalg.norm(delta,axis=1)
     correction=delta*((1-lengths[ids]/np.maximum(length,1e-12))*stiffness/np.maximum(mov[a]+mov[b],1))[:,None]
     p[a]+=correction*mov[a,None];p[b]-=correction*mov[b,None]
   p=collide(p,caprows);p=distance_clamp(p,target)
 p_render=p[mapping];target_render=target[mapping];offset=p_render-target_render
 gap=surface_gaps(p_render,skin);before=surface_gaps(target_render,skin)
 error=np.linalg.norm(p-target,axis=1)-d['max_distances']
 root_drift=np.linalg.norm(p[fixed]-target[fixed],axis=1).max()
 remaining=np.linalg.norm(collide(p.copy(),caprows)-p,axis=1)
 row=dict(animation=label,frame=frame,settle_seconds=3,before=before,settled=gap,maximum_rear_motion_m=float(np.linalg.norm(offset[posterior],axis=1).max()),median_rear_motion_m=float(np.median(np.linalg.norm(offset[posterior],axis=1))),median_rear_drop_m=float(np.median(-offset[posterior,2])),maximum_fixed_root_drift_m=float(root_drift),maximum_distance_excess_m=float(error.max()),remaining_capsule_penetration_m=float(remaining.max()),initial_collision_lift_m=float(initial_projection[:,2].max()),worst_collision_rest=rest[remaining.argmax()].tolist(),worst_collision_travel=float(d['max_distances'][remaining.argmax()]))
 assert root_drift<1e-8 and error.max()<1e-8
 rows.append(row);positions[f'{label}_{frame}']=p_render
 print('FREE_HAIR_CPU',row,flush=True)
np.savez(ROOT/'build/free_hair_settled_positions.npz',**positions)
assert max(r['maximum_rear_motion_m'] for r in rows)>.012,'Gravity remains constrained to old 8mm band'
assert all(r['settled']['inside_samples']/max(r['settled']['covered_samples'],1)<.01 for r in rows),'More than isolated minor CPU clipping remains'
assert max(r['remaining_capsule_penetration_m'] for r in rows)<.002,'Collision and travel constraints conflict'
report=dict(status='pass',final_package_sha256=hashlib.sha256((ROOT/'build/back_hair_candidate_v1.1.7.tpac').read_bytes()).hexdigest(),root_positions=int(fixed.sum()),maximum_solver_travel_m=float(d['max_distances'].max()),bending_stiffness=.18,gravity=7,poses=rows,game_test_verified=False,acceptance='User prioritizes natural silhouette and accepts visually minor clipping; CPU rear-ray inside sample fraction must remain below 1% per sampled pose. This does not measure visual severity in game.',scope='Approximate CPU constraint/gravity/capsule relaxation of seven static native poses, 120Hz for 3s. No engine solver, animated inertia, wind, dummy triangle collisions, body sliders or IK. A diagnostic, not game acceptance.')
(ROOT/'reports/free_hair_diagnostic.json').write_text(json.dumps(report,indent=2))
print('FREE_HAIR_DIAGNOSTIC_PASSED',flush=True)
