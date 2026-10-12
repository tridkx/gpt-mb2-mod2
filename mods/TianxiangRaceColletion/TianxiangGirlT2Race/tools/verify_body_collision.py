"""Check whole T2 protected shorts surface against the capsule union."""
import json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cfg=json.loads((R/'tools/model_config.json').read_text());a=np.load(R/'build/fitted_model.npz')
name=cfg['shorts_part'];p=a[name+'_p'];tri=p[a[name+'_f']];samples=[]
for i in range(5):
    for j in range(5-i):
        bary=np.array([i,j,4-i-j])/4;samples.append((tri*bary[None,:,None]).sum(1))
samples=np.concatenate(samples);lo,hi=cfg['shorts_height_band_m'];samples=samples[(samples[:,2]>lo)&(samples[:,2]<hi)]
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules'];outside=np.full(len(samples),1e9)
for c in caps:
    a,b=np.array(c['endpoints_m']);v=b-a;t=np.clip((samples-a)@v/(v@v),0,1)
    outside=np.minimum(outside,np.linalg.norm(samples-a-t[:,None]*v,axis=1)-c['radius_m'])
report=dict(status='pass' if int((outside>1e-7).sum())==0 else 'fail',version=cfg['version'],capsules=len(caps),source_height_band_m=[lo,hi],samples=len(samples),
            outside_samples=int((outside>1e-7).sum()),maximum_sample_exposure_m=float(np.maximum(outside,0).max()),
            scope='Whole protected shorts band; triangle interiors, edges and vertices versus rest capsule union; not engine cloth proof')
(R/'reports/body_collision_validation.json').write_text(json.dumps(report,indent=2))
assert report['outside_samples']==0,report
print('BODY_COVERAGE_PASS',report)
