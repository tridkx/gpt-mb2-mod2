"""Create T2-specific measured landmarks and semantic part configuration."""
import json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];a=np.load(R/'build/source_samples.npz')
skin=a['mesh_13_1062969_p'];hand=a['mesh_06_523091_p'];legs=a['mesh_05_436959_p'];pants=a['mesh_02_302131_p']
def centre(p,mask):
    q=p[mask];assert len(q)>3
    return np.median(q,axis=0)
shoulder=centre(skin,(skin[:,0]>.111)&(skin[:,0]<.129))
elbow=centre(skin,(skin[:,0]>.236)&(skin[:,0]<.254))
wrist=centre(hand,(hand[:,0]>.35)&(hand[:,0]<.385)&(hand[:,2]>.827))
palm=centre(hand,(hand[:,0]>.39)&(hand[:,0]<.405)&(hand[:,2]>.775)&(hand[:,2]<.82))
tip=centre(hand,(hand[:,0]>.416)&(hand[:,2]<.765))
knee=centre(legs,(legs[:,0]>0)&(legs[:,2]>.42)&(legs[:,2]<.46))
ankle=centre(legs,(legs[:,0]>0)&(legs[:,2]>.065)&(legs[:,2]<.095))
hip=np.array([.075,float(np.median(pants[(pants[:,0]>0)&(pants[:,2]>.76),1])),.813])
toe=np.array([ankle[0],.057,.012])
S=np.zeros((28,3));S[0]=[0,0,.813]
S[9]=[0,-.003,.895];S[10]=[0,-.008,.981];S[11]=[0,-.015,1.072]
S[12]=[0,-.022,1.157];S[13]=[0,-.024,1.233]
for sign,base in [(-1,1),(1,5)]:
    for i,p in enumerate([hip,knee,ankle,toe]):S[base+i]=p*np.array([sign,1,1])
for sign,start in [(-1,14),(1,21)]:
    clavicle=np.array([.034,shoulder[1],shoulder[2]])
    for i,p in enumerate([clavicle,shoulder,(shoulder+elbow)/2,elbow,(elbow+wrist)/2,wrist,palm]):S[start+i]=p*np.array([sign,1,1])
cfg=dict(id='TianxiangGirlT2Race',version='v0.1.2',race='txgirl2',skeleton='txgirl2_skeleton',skin_min_scale=1.0,
         cloth_enabled=True,cloth_lods=[0,1],lod_multipliers=[1,.7,.45,.25],minimum_ratios={'tunic_D':1.0},
         landmarks_m=S.tolist(),align_arm_bind_axes=True,
         hand_weight_tips_m={'l_hand':(tip*[-1,1,1]).tolist(),'r_hand':tip.tolist()},
         source_height_range_m=[1.32,1.35],weight_softness_m=.025,
         skirt_source='mesh_12_947881',skirt_object='txgirl2_part_12',legs_sources=['mesh_02_302131','mesh_05_436959'],
         collision_parts=['txgirl2_part_02','txgirl2_part_05'],shorts_part='txgirl2_part_02',hand_part='txgirl2_part_06',
         cloth_travel_slope=.45,cloth_max_travel_m=.18,cloth_root_band_m=.012,
         collision_clearance_m=.0012,shorts_local_capsules=64,shorts_capsule_clearance_m=.0018,shorts_height_band_m=[.55,.855],
         gross_motion_extension_limit=6.0,cloth_travel_shortfall_limit_m=.005,fixed_root_overlap_limit_m=.005)
(R/'tools/model_config.json').write_text(json.dumps(cfg,indent=2))
(R/'reports/landmark_measurements.json').write_text(json.dumps(dict(source='Own T2 source samples in metres; skin cross-section medians for shoulder, elbow, wrist, palm, knee and ankle; internal torso/hip centres chosen inside measured body',
         shoulder=shoulder.tolist(),elbow=elbow.tolist(),wrist=wrist.tolist(),palm=palm.tolist(),hand_tip=tip.tolist(),knee=knee.tolist(),ankle=ankle.tolist(),landmarks=S.tolist()),indent=2))
print('T2_LANDMARKS',shoulder,elbow,wrist,palm,knee,ankle)
