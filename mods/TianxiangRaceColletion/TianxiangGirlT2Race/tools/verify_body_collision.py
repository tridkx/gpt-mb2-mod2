"""Protect shorts in rest, native actions and actual captured creation poses."""
import json,numpy as np,hashlib
from collision_helpers import R,cfg,protection_mesh,native_skins,surface_samples,outside_union,published_capsules
mesh=protection_mesh();caps=published_capsules();rows={}
for label,frame,skin in native_skins():
    p=surface_samples(mesh,skin,grid=9);outside=outside_union(p,caps,skin)
    row=rows.setdefault(label,dict(pose=label,frames=0,samples_per_frame=len(p),worst_frame=frame,outside_samples=0,maximum_sample_exposure_m=0.0,minimum_cover_margin_m=1e9))
    row['frames']+=1;count=int((outside>1e-7).sum());exposure=float(np.maximum(outside,0).max())
    row['minimum_cover_margin_m']=min(row['minimum_cover_margin_m'],float(-outside.max()))
    if (exposure,count)>(row['maximum_sample_exposure_m'],row['outside_samples']):row.update(worst_frame=frame,outside_samples=count,maximum_sample_exposure_m=exposure)
report=dict(status='pass' if all(row['outside_samples']==0 for row in rows.values()) else 'fail',version=cfg['version'],capsules=len(caps),source_height_band_m=cfg['shorts_height_band_m'],samples=sum(row['frames']*row['samples_per_frame'] for row in rows.values()),outside_samples=sum(row['outside_samples'] for row in rows.values()),maximum_sample_exposure_m=max(row['maximum_sample_exposure_m'] for row in rows.values()),poses=list(rows.values()),scope='Final byte-weighted whole protected shorts surface; triangle interiors grid 9; full run cycle, 32 samples of each other native action, 11 actual creation poses; published XML capsule union; not engine cloth proof')
report['final_package_sha256']=hashlib.sha256((R/'module/TianxiangGirlT2Race/AssetPackages/txgirl2.tpac').read_bytes()).hexdigest()
report['collision_xml_sha256']=hashlib.sha256((R/'module/TianxiangGirlT2Race/ModuleData/cloth_bodies.xml').read_bytes()).hexdigest()
(R/'reports/body_collision_validation.json').write_text(json.dumps(report,indent=2))
print('POSED_BODY_COVERAGE',[(r['pose'],r['outside_samples'],round(r['maximum_sample_exposure_m'],5)) for r in rows.values()])
assert report['outside_samples']==0,report
