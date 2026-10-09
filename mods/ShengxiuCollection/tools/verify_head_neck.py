"""Final TPAC rear gap plus coherent head transform and continuous neck seams."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'tools/verify_hair_shape.py').read_text()
code=code.replace('hair_shape','head_neck').replace('v1.1.5','v1.1.6')
code=code.replace('head_neck_baseline_v1.1.4','hair_shape_baseline_v1.1.4')
code=code.replace('from head_neck_analysis','from hair_shape_analysis')
code=code.replace('reports/hair_clearance_validation.json','reports/hair_shape_validation.json').replace('>.012','>.008')
exec(compile(code,__file__,'exec'))
from hair_shape_analysis import parse_skeljson,parse_animjson,skin_matrices,lbs
def dense(m):
 w=np.zeros((len(m['pos']),28));np.add.at(w,(np.arange(len(w))[:,None],m['bi']),m['bw']/255);return w
checks=[]
for lod in range(4):
 ms=[m for m in allmeshes if m['lod']==lod]
 eye=next(m for m in ms if m['name']=='sx_mingyu_head_07');reference=dense(eye)[0]
 for name in ['sx_mingyu_head_03','sx_mingyu_head_07','sx_mingyu_head_08','sx_mingyu_head_09','sx_mingyu_head_11']:
  m=next(m for m in ms if m['name']==name);w=dense(m)
  ids=m['pos'][:,2]>=1.515 if name=='sx_mingyu_head_08' else np.ones(len(w),bool)
  assert abs(w[ids]-reference).max()<1e-8,(lod,name,'nonuniform face transform')
 face=next(m for m in ms if m['name']=='sx_mingyu_head_08');body=next(m for m in ms if m['name']=='sx_mingyu_body_02')
 d,idx=cKDTree(body['pos']).query(face['pos']);shared=d<1e-6
 assert shared.any();error=float(abs(dense(face)[shared]-dense(body)[idx[shared]]).max())
 assert error<1e-8,(lod,'neck seam weight mismatch',error)
 checks.append({'lod':lod,'shared_neck_vertices':int(shared.sum()),'shared_weight_max_error':error})
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));anim=parse_animjson(json.loads((ROOT/'reports/idle.json').read_text()));pitches=[]
for frame in range(max(1,anim['start']),anim['frames']):
 skin=skin_matrices(rig,anim,frame)
 old=skin[13,:3,1];new=reference[12]*skin[12,:3,1]+reference[13]*old
 pitches.append([float(np.degrees(np.arctan2(v[2],np.linalg.norm(v[:2])))) for v in [old,new]])
oldmax=float(abs(np.array(pitches)[:,0]).max());newmax=float(abs(np.array(pitches)[:,1]).max());assert newmax<oldmax*.6
report['head_neck_checks']={'all_lods_face_eye_ornament_uniform_transform':True,'seams':checks,'idle_old_max_forward_axis_pitch_degrees':oldmax,'idle_new_max_forward_axis_pitch_degrees':newmax,'hair_forward_reduction_m':.045,'rear_cloth_limit_m':.008}
report['limitations']=report['limitations'].replace('Rear travel is 12mm','Rear travel is 8mm')+' Neck crease appearance requires side close-up review and game confirmation.'
(ROOT/'reports/head_neck_validation.json').write_text(json.dumps(report,indent=2))
print('HEAD_NECK_COHERENCE_VERIFIED',oldmax,newmax,checks)
