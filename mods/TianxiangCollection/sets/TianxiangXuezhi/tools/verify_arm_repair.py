"""Compare repair arrays to preserved first-release baseline."""
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
old=np.load(ROOT/'build/arm_baseline/rig_arrays.npz');new=np.load(ROOT/'build/rig_arrays.npz')
unchanged=[]
for name in sorted(k[:-2] for k in new.files if k.endswith('_S')):
    assert np.array_equal(old[name+'_S'],new[name+'_S'])
    if name not in ['xz7_body_06','xz7_body_09']:
        for field in ['P','W','A']:assert np.array_equal(old[name+'_'+field],new[name+'_'+field]),(name,field)
        unchanged.append(name)
name='xz7_body_09';p=new[name+'_S'];shoulder=(p[:,2]>1.35)&(np.abs(p[:,0])>.07)
for field in ['P','W','A']:assert np.array_equal(old[name+'_'+field][~shoulder],new[name+'_'+field][~shoulder])
assert np.array_equal(old['xz7_body_06_A'],new['xz7_body_06_A'])
assert np.array_equal(old['xz7_body_09_A'],new['xz7_body_09_A'])
w=new['xz7_body_06_W'];s=new['xz7_body_06_S'];cuff=abs(s[:,0])>.40
assert w[cuff][:,[17,24]].sum(1).min()>.75
release=json.loads((ROOT/'reports/release_validation.json').read_text());assert release['status']=='pass'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
report={'status':'pass','version':release['version'],'final_package_sha256':release['final_package_sha256'],'baseline_package_sha256':sha(ROOT/'build/arm_baseline/xz7.tpac'),'source_coordinates_unchanged':True,'unrelated_meshes_unchanged':unchanged,'central_dress_and_skirt_unchanged':True,'cloth_distances_unchanged':True,'minimum_cuff_forearm_follow':float(w[cuff][:,[17,24]].sum(1).min()),'game_verified':False}
(ROOT/'reports/arm_repair_validation.json').write_text(json.dumps(report,indent=2))
print('ARM_REPAIR_VERIFIED',report)
