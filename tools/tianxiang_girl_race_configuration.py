"""Measure semantic parts and source-proportioned bind joints for girl races."""
import json
import numpy as np

def configure(R):
    a=np.load(R/'build/source_samples.npz')
    parts=sorted(json.loads((R/'input/parts.json').read_text()),key=lambda r:r['name'])
    pos={r['name']:a[r['name']+'_p'] for r in parts}
    body=[r['name'] for r in parts if r['tex']=='body_D']
    # Identify anatomy by measured extents rather than source object numbers.
    hand_name=max(body,key=lambda n:np.ptp(pos[n][:,0]))
    skin_name=max(body,key=lambda n:pos[n][:,2].max())
    leg_name=min(body,key=lambda n:pos[n][:,2].min())
    pants_name=next(r['name'] for r in parts if r['tex'].startswith('pants_D'))
    skirt_name=min((r['name'] for r in parts if r['tex'].startswith('tunic_D')),key=lambda n:pos[n][:,2].min())
    skin=pos[skin_name];hand=pos[hand_name]
    legs=np.concatenate([pos[leg_name],pos[pants_name]])
    pants=pos[pants_name]
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
    hip=centre(pants,(pants[:,0]>.04)&(pants[:,0]<.11)&(pants[:,2]>.785)&(pants[:,2]<.835))
    neck=centre(skin,(abs(skin[:,0])<.06)&(skin[:,2]>skin[:,2].max()-.02))
    eyes=pos[next(r['name'] for r in parts if r['tex']=='eye_D')]
    head=np.median(eyes,axis=0);head[0]=0;head[1]=neck[1]
    S=np.zeros((28,3));S[0]=[0,hip[1],hip[2]]
    for i,t in zip([9,10,11],[.30,.62,1.]):S[i]=[0,hip[1]*(1-t)+shoulder[1]*t,hip[2]*(1-t)+shoulder[2]*t]
    S[12]=[0,neck[1],neck[2]];S[13]=head
    toe=np.array([ankle[0],float(pants[:,1].max()*.75),float(pants[:,2].min()+.012)])
    for sign,base in [(-1,1),(1,5)]:
        for i,p in enumerate([hip,knee,ankle,toe]):S[base+i]=p*np.array([sign,1,1])
    for sign,start in [(-1,14),(1,21)]:
        clavicle=np.array([shoulder[0]*.285,shoulder[1],shoulder[2]])
        for i,p in enumerate([clavicle,shoulder,(shoulder+elbow)/2,elbow,(elbow+wrist)/2,wrist,palm]):S[start+i]=p*np.array([sign,1,1])
    ident=R.name;n=int(ident.removeprefix('TianxiangGirlT').removesuffix('Race'));race=f'txgirl{n}'
    obj=lambda name:race+'_part_'+str([r['name'] for r in parts].index(name)).zfill(2)
    height=float(np.ptp(np.concatenate(list(pos.values()))[:,2]))
    cfg=dict(id=ident,version='v0.1.0',race=race,skeleton=race+'_skeleton',skin_min_scale=1.0,
        cloth_enabled=False,cloth_lods=[],lod_multipliers=[1,.7,.45,.25],
        minimum_ratios={r['tex']:1. for r in parts if r['tex'].startswith('tunic_D')},
        landmarks_m=S.tolist(),align_arm_bind_axes=True,hand_weight_tips_m={'l_hand':(tip*[-1,1,1]).tolist(),'r_hand':tip.tolist()},
        source_height_range_m=[height-.002,height+.002],weight_softness_m=.025,
        upper_skin_source=skin_name,skirt_source=skirt_name,skirt_object=obj(skirt_name),legs_sources=[pants_name,leg_name],
        collision_parts=[obj(pants_name),obj(leg_name)],shorts_part=obj(pants_name),hand_part=obj(hand_name),
        cloth_root_band_m=.012,cloth_travel_slope=.45,cloth_max_travel_m=.18)
    (R/'tools/model_config.json').write_text(json.dumps(cfg,indent=2))
    report=dict(source='Own FBX samples in metres, measured cross-section medians and semantic part extents',
        source_height_m=height,semantic_parts=dict(hand=hand_name,upper_skin=skin_name,legs=leg_name,pants=pants_name,skirt=skirt_name),
        shoulder=shoulder.tolist(),elbow=elbow.tolist(),wrist=wrist.tolist(),palm=palm.tolist(),knee=knee.tolist(),ankle=ankle.tolist(),landmarks=S.tolist())
    (R/'reports/landmark_measurements.json').write_text(json.dumps(report,indent=2))
    print('MEASURED_CONFIGURATION',ident,report['semantic_parts'])
