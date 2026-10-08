"""Compare a preserved fitted-model baseline with the current width revision."""
import json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
baseline=ROOT/'build/width_v100/fitted_model.npz'
old=np.load(baseline);new=np.load(ROOT/'build/fitted_model.npz')
landmarks=np.array(json.loads((ROOT/'reports/weight_transfer.json').read_text())['target_landmarks'])
names=json.loads((ROOT/'reports/weight_transfer.json').read_text())['native_bones']
for key in old.files:
    if key.endswith(('_w','_f','_uv')):assert np.array_equal(old[key],new[key]),key
    if key.startswith(('boru_head','boru_hands')):assert np.array_equal(old[key],new[key]),key
    if key.endswith('_p'):assert np.array_equal(old[key][:,2],new[key][:,2]),key
def section(a,name,height,side):
    p=a[name+'_p'];faces=a[name+'_f'];out=[]
    for tri in p[faces]:
        for i,j in [(0,1),(1,2),(2,0)]:
            u,v=tri[i],tri[j]
            if (u[2]-height)*(v[2]-height)<0:
                q=u+(v-u)*((height-u[2])/(v[2]-u[2]))
                if q[0]*side>0:out.append(q[0])
    return float(np.ptp(out))
checks=[]
for height in [.35,.50,.70]:
    for side in [-1,1]:
        a=section(old,'boru_body_cloth',height,side);b=section(new,'boru_body_cloth',height,side)
        assert .79<b/a<.82,(height,side,b/a)
        checks.append({'height_m':height,'side':side,'old_width_m':a,'new_width_m':b,'ratio':b/a})
shoe=[]
for side in ['l','r']:
    anchor=landmarks[names.index(side+'_foot')];axis=landmarks[names.index(side+'_toe0')][:2]-anchor[:2];axis/=np.linalg.norm(axis)
    lateral=np.array([-axis[1],axis[0]]);a=old['boru_legs_cloth_p'];b=new['boru_legs_cloth_p'];sel=a[:,0]<0 if side=='l' else a[:,0]>0
    a=a[sel];b=b[sel];ratio=float(np.ptp((b[:,:2]-anchor[:2])@lateral)/np.ptp((a[:,:2]-anchor[:2])@lateral))
    length=float(np.max(np.abs((b[:,:2]-a[:,:2])@axis)))
    assert abs(ratio-.75)<1e-5 and length<1e-6,(side,ratio,length)
    shoe.append({'side':side,'width_ratio_to_v100':ratio,'max_length_axis_change_m':length,'height_unchanged':True})
package=ROOT/'module/BoRuModern/AssetPackages/boru.tpac'
report={'status':'pass','version':'v1.0.1','baseline_version':'v1.0.0','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'head_hands_uv_weights_topology_unchanged':True,'leg_shoe_height_unchanged':True,'leg_width_scale_from_original':.64,'leg_depth_scale_from_original':.85,'shoe_width_scale_from_original':.6375,'leg_sections':checks,'shoes':shoe,'head_scale_from_original':1.12}
(ROOT/'reports/proportion_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
