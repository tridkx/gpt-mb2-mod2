"""Measure head drift relative to the neck frame; compare old and repaired weights."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices
sys.path.insert(0,str(ROOT.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
from scipy.spatial import cKDTree
for name in sys.argv[1:] or ['02_Baifeng','03_Suwen']:
 r=ROOT/'sets'/name;cfg=json.loads((r/'tools/model_config.json').read_text(encoding='utf-8'))
 a=np.load(r/'build/rig_arrays.npz');manifest=json.loads((r/'build/rig_manifest.json').read_text())
 eye=next(x['object'] for x in manifest if x['texture_key']=='eye')
 p=a[eye+'_P'];center=p.mean(0);old=a[eye+'_fitW'].mean(0);new=a[eye+'_W'].mean(0)
 final=next(m for f in (r/'build/final_export/geo').glob('*.bin') for m in read_geo(f) if m['name']==eye)
 finalw=np.zeros((len(final['pos']),28));np.add.at(finalw,(np.arange(len(finalw))[:,None],final['bi']),final['bw']/255.)
 assert np.max(abs(finalw[:,12]-.7))<1/255 and np.max(abs(finalw[:,13]-.3))<1/255
 final_neck_weight=float(finalw[:,12].mean())
 face=next(x['object'] for x in manifest if x['texture_key']=='face')
 face_checks=[]
 for file in (r/'build').glob('final_export*/geo/*.bin'):
  for m in read_geo(file):
   if m['name'].split('.lod')[0]!=face:continue
   distance,ids=cKDTree(a[face+'_P']).query(m['pos'])
   protected=a[face+'_S'][ids,2]>=1.5481
   weights=np.zeros((len(m['pos']),28));np.add.at(weights,(np.arange(len(weights))[:,None],m['bi']),m['bw']/255.)
   error=float(abs(weights[protected]-finalw[0]).max());assert error<1e-7,(name,m['lod'],'chin/face not following same transform',error)
   face_checks.append({'lod':m['lod'],'protected_face_vertices':int(protected.sum()),'maximum_weight_difference_from_eye':error})
 assert {check['lod'] for check in face_checks}=={0,1,2,3}
 rig=parse_skeljson(json.loads((r/'reports/human_skeleton.json').read_text()));motions=[]
 for label in ['idle','run','bow','riding']:
  anim=parse_animjson(json.loads((r/'reports'/f'{label}.json').read_text()));before=[];after=[]
  for frame in range(max(1,anim['start']),anim['frames']):
   m=skin_matrices(rig,anim,frame);v=np.einsum('nij,j->ni',m[:,:3,:3],center)+m[:,:3,3]
   # Difference from a head centered over this model's neck frame, in neck-local axes.
   before.append(abs(((old@v-v[12])@m[12,:3,:3])[0]))
   after.append(abs(((new@v-v[12])@m[12,:3,:3])[0]))
  b=float(max(before));c=float(max(after));assert c<=b*.301+1e-7
  motions.append({'label':label,'old_max_lateral_drift_m':b,'new_max_lateral_drift_m':c,'frames_checked':len(after)})
 baseline=r/'build/before_head_repair.npz';rest_error=None
 if baseline.exists():
  olddata=np.load(baseline);rest_error=max(float(abs(a[k]-olddata[k]).max()) for k in olddata.files if k.endswith('_P'))
  assert rest_error<1e-9
 package=r/'module/ShengxiuCollection/AssetPackages'/f"{cfg['prefix']}.tpac"
 report={'status':'pass','package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
  'rest_geometry_max_change_m':rest_error,'neck_follow_fraction':cfg['runtime_head_neck_follow'],
  'final_tpac_eye_neck_weight':final_neck_weight,'final_quantized_weights_verified':True,
  'chin_and_face_uniform_transform_verified':face_checks,
  'measure':'lateral head-center drift relative to neck coordinate frame; native animation rotations retained',
  'motions':motions,'scope':'offline skeletal motion; game test by user'}
 (r/'reports/head_follow_validation.json').write_text(json.dumps(report,indent=2));print(name,motions)
