"""Measure the added arm angle and torso dimensions on generated game geometry."""
from pathlib import Path
import json,sys,hashlib,subprocess
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'D:\gpt-mb2-mod\tools')
from georead import read_geo

before=np.load(ROOT/'build/posture_baseline/rig_arrays.npz')
after=np.load(ROOT/'build/rig_arrays.npz')
assert set(before.files)==set(after.files)
for key in before.files:
    if key in {'source','target','world'} or key.endswith(('_S','_W','_A')):
        assert np.array_equal(before[key],after[key]),key
    if key.endswith('_P') and key.startswith(('tx5_head_','tx5_legs_')):
        assert np.array_equal(before[key],after[key]),key

source=after['tx5_body_07_S'];weights=after['tx5_body_07_W']
hand_angles=[];radius_errors=[]
for bone,bones,sign in [(15,slice(14,21),-1),(22,slice(21,28),1)]:
    chosen=(source[:,0]*sign>.40)&(source[:,2]<1.07)&(weights[:,bones].sum(1)>.99999)
    pivot=after['target'][bone]
    old=before['tx5_body_07_P'][chosen]-pivot;new=after['tx5_body_07_P'][chosen]-pivot
    angle=np.degrees(np.arctan2(old[:,1]*new[:,2]-old[:,2]*new[:,1],old[:,1]*new[:,1]+old[:,2]*new[:,2]))
    hand_angles.extend(angle.tolist())
    radius_errors.extend(np.abs(np.linalg.norm(old,axis=1)-np.linalg.norm(new,axis=1)).tolist())
assert len(hand_angles)>20
assert np.max(np.abs(np.array(hand_angles)-20))<.01
assert max(radius_errors)<1e-5

p=after['tx5_body_00_P'];old=before['tx5_body_00_P'];s=after['tx5_body_00_S']
band=(s[:,2]>1.10)&(s[:,2]<1.29)
width=band&(np.abs(s[:,0])>.04)&(np.abs(s[:,0])<.12)
width_ratio=float(np.median(np.abs(p[width,0]/old[width,0])))
core=band&(np.abs(s[:,0])<.08)&(np.abs(old[:,1]-.02)>.02)
depth_ratio=float(np.median((p[core,1]-.02)/(old[core,1]-.02)))
assert width.sum()>10 and core.sum()>10
assert abs(width_ratio-1.08)<.001 and abs(depth_ratio-1.05)<.001

skirt_source=after['tx5_body_03_S'];lower=skirt_source[:,2]<=.94
assert np.array_equal(after['tx5_body_03_P'][lower],before['tx5_body_03_P'][lower])

meshes={s['name']:s for f in (ROOT/'build/final_export/geo').glob('*.bin') for s in read_geo(f)}
exported=meshes['tx5_body_00']['pos']
distance=cKDTree(exported).query(p[width|core])[0]
assert distance.max()<2e-6,float(distance.max())
baseline_bytes=subprocess.run(['git','show','v1.2.0:module/TianxiangT5/AssetPackages/tx5.tpac'],
                              cwd=ROOT,check=True,capture_output=True).stdout
baseline_hash=hashlib.sha256(baseline_bytes).hexdigest()
assert hashlib.sha256((ROOT/'build/posture_baseline/tx5.tpac').read_bytes()).hexdigest()==baseline_hash
result={'version':'v1.3.0','baseline_version':'v1.2.0',
        'arm_total_forward_degrees':26,'measured_extra_arm_forward_degrees':float(np.median(hand_angles)),
        'max_arm_radius_change_mm':float(max(radius_errors)*1000),
        'measured_torso_width_scale':width_ratio,'measured_torso_depth_scale':depth_ratio,
        'weights_and_cloth_vertex_data_unchanged':True,'head_and_legs_unchanged':True,
        'lower_skirt_geometry_unchanged':True,'sampled_torso_matches_final_tpac':True,
        'baseline_package_sha256':baseline_hash,
        'final_package_sha256':hashlib.sha256((ROOT/'module/TianxiangT5/AssetPackages/tx5.tpac').read_bytes()).hexdigest(),
        'game_test_verified':False}
(ROOT/'reports/posture_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
