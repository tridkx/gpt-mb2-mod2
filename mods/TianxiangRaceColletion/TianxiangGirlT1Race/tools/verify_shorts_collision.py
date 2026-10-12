"""Compare the union of all leg capsules against the whole shorts height band."""
import json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];data=np.load(R/'build/fitted_model.npz')
p=data['txgirl1_part_04_p'];tri=p[data['txgirl1_part_04_f']]
samples=np.concatenate([p,tri.mean(1),(tri[:,0]+tri[:,1])/2,(tri[:,1]+tri[:,2])/2,(tri[:,2]+tri[:,0])/2])
samples=samples[(samples[:,2]>.55)&(samples[:,2]<.835)];rows={}
for label,file in [('before',R/'tools/shorts_collision_baseline.json'),('after',R/'reports/cloth_collision.json')]:
    outside=np.full(len(samples),1e9)
    for c in json.loads(file.read_text())['capsules']:
        a,b=np.array(c['endpoints_m']);v=b-a;t=np.clip((samples-a)@v/(v@v),0,1)
        outside=np.minimum(outside,np.linalg.norm(samples-a-t[:,None]*v,axis=1)-c['radius_m'])
    rows[label]={'outside_capsule_samples':int((outside>0).sum()),'samples':len(samples),
                 'maximum_sample_exposure_m':float(np.maximum(outside,0).max()),
                 'outside_sample_bbox_m':samples[outside>0].min(0).tolist()+samples[outside>0].max(0).tolist() if (outside>0).any() else None}
assert rows['after']['outside_capsule_samples']<rows['before']['outside_capsule_samples']
assert rows['after']['maximum_sample_exposure_m']<rows['before']['maximum_sample_exposure_m']
report={'status':'pass_improved_rest_coverage','version':json.loads((R/'tools/model_config.json').read_text())['version'],
        'rest_short_surface_screen':rows,'source_height_band_m':[.55,.835],
        'scope':'Whole fitted shorts band versus capsule union. Remaining exposure is reported, not hidden by fitting only selected capsule bands; not a game cloth solver result',
        'game_retest_pending':True}
(R/'reports/shorts_collision_validation.json').write_text(json.dumps(report,indent=2));print('SHORTS_COVERAGE_SCREEN',rows)
