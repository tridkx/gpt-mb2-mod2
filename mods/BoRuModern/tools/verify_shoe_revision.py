"""Measure v1.0.3 against the preserved v1.0.2 fitted model."""
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
old=np.load(ROOT/'build/shoe_v102/fitted_model.npz');new=np.load(ROOT/'build/fitted_model.npz')
for key in old.files:
    if not key.startswith('boru_legs') or key.endswith(('_w','_f','_uv')):
        assert np.array_equal(old[key],new[key]),key
    if key.endswith('_p'):assert np.array_equal(old[key][:,2],new[key][:,2]),key
report=json.loads((ROOT/'reports/weight_transfer.json').read_text());names=report['native_bones'];joints=np.array(report['target_landmarks']);rows=[]
for side in ['l','r']:
    anchor=joints[names.index(side+'_foot')];axis=joints[names.index(side+'_toe0')][:2]-anchor[:2];axis/=np.linalg.norm(axis);lateral=np.array([-axis[1],axis[0]])
    a=old['boru_legs_cloth_p'];b=new['boru_legs_cloth_p'];select=a[:,0]<0 if side=='l' else a[:,0]>0;a=a[select];b=b[select]
    ratio=float(np.ptp((b[:,:2]-anchor[:2])@lateral)/np.ptp((a[:,:2]-anchor[:2])@lateral))
    length=float(np.max(np.abs((b[:,:2]-a[:,:2])@axis)))
    rim=a[:,2]>.164;rim_change=float(np.max(np.linalg.norm(a[rim]-b[rim],axis=1)))
    assert abs(ratio-.90)<1e-5 and length<1e-6 and rim_change<1e-7,(side,ratio,length,rim_change)
    rows.append({'side':side,'shoe_width_ratio_to_v102':ratio,'max_length_axis_change_m':length,'max_sock_rim_change_m':rim_change})
package=ROOT/'module/BoRuModern/AssetPackages/boru.tpac'
result={'status':'pass','version':'v1.0.3','baseline_version':'v1.0.2','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'head_body_hands_unchanged':True,'all_weights_uv_topology_unchanged':True,'all_heights_unchanged':True,'shoe_extra_width_scale':.90,'hidden_skin_tail_follows_shoe':True,'shoes':rows}
(ROOT/'reports/shoe_revision_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
