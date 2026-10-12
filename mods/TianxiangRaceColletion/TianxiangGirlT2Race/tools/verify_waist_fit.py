"""Compare published collision pressure at the active waist against v0.1.1."""
import json,numpy as np,hashlib
from collision_helpers import R,cfg,native_skins,outside_union,published_capsules
from baker.animation import lbs
m=next(json.loads(p.read_text()) for p in (R/'build/cloth_inputs').glob('*.mesh.json') if json.loads(p.read_text())['lod']==0)
p=np.array(m['positions']);mask=(p[:,2]>.65)&(p[:,2]<.86)&(np.array(m['alpha'])>0)
old=json.loads((R/'reports/history/v0.1.1/cloth_collision.json').read_text())['capsules'];new=published_capsules();rows=[]
for label,frame,skin in native_skins():
    if label not in ['rest','captured_creation']:continue
    q=lbs(p,np.array(m['bones']),np.array(m['weights']),skin)[mask];values=[]
    for caps in [old,new]:
        push=np.maximum(-outside_union(q,caps,skin),0);values.append(dict(maximum_m=float(push.max()),mean_m=float(push.mean())))
    rows.append(dict(pose=label,frame=frame,baseline=values[0],current=values[1]))
package_sha=hashlib.sha256((R/'module/TianxiangGirlT2Race/AssetPackages/txgirl2.tpac').read_bytes()).hexdigest()
baseline_sha=json.loads((R/'reports/history/v0.1.1/static_cloth_proxy.json').read_text())['final_package_sha256']
assert package_sha==baseline_sha,'Collision fit must retain the accepted source/binding/cloth payload'
assert len(new)<=128,'Local shader uploads one capsule per thread; THREAD_COUNT=128'
report=dict(final_package_sha256=package_sha,baseline_package_sha256=baseline_sha,version=cfg['version'],status='pass' if all(r['current']['maximum_m']<r['baseline']['maximum_m'] and r['current']['mean_m']<r['baseline']['mean_m'] for r in rows) else 'fail',collision_xml_sha256=hashlib.sha256((R/'module/TianxiangGirlT2Race/ModuleData/cloth_bodies.xml').read_bytes()).hexdigest(),capsules=len(new),rows=rows,scope='Upper active skirt rest-reference pressure by posed published capsules; measures collision displacement demand, not game cloth separation')
(R/'reports/waist_fit_validation.json').write_text(json.dumps(report,indent=2));print('WAIST_FIT',report['status'],[(r['pose'],r['frame'],r['baseline'],r['current']) for r in rows]);assert report['status']=='pass'
