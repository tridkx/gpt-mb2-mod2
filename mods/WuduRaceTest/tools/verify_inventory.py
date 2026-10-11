"""Sample native inventory poses against the final custom skeleton and meshes."""
import json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build'
sys.path[:0]=[str(WS/'tools/asset_helpers/previewer'),str(WS/'tools/asset_helpers/tools')]
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
from georead import read_geo
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));inverse=np.linalg.inv(rig['restWorld'])
groups=[g for path in (B/'final_export0/geo').glob('*.bin') for g in read_geo(path) if g['name'].startswith('wdr_part_')]
rows=[]
for label in ['inventory_idle','facegen_male','facegen_female']:
    anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()));samples=[]
    for frame in sorted(set(np.linspace(anim['start'],anim['frames']-1,24).astype(int))):
        world=rig['restWorld'].copy()
        for i in range(rig['boneCount']):
            local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame]) if i<28 else local[:3,:3];parent=rig['parent'][i]
            if parent<0:local[:3,3]+=anim['rootPos'][frame]
            world[i]=local if parent<0 else world[parent]@local
        skin=world@inverse
        points={g['name']:lbs(g['pos'],g['bi'],g['bw'],skin) for g in groups}
        assert all(np.isfinite(p).all() for p in points.values())
        # Express wrists in the moving torso's bind coordinate system.
        local_wrists=[(np.linalg.inv(skin[11])@np.r_[world[i,:3,3],1])[:3].tolist() for i in [19,26]]
        samples.append(dict(frame=int(frame),wrists_torso_bind_m=local_wrists))
        if frame==anim['start']:np.savez_compressed(B/(label+'_preview.npz'),**points)
    rows.append(dict(pose=label,frames=len(samples),samples=samples))
cfg=json.loads((R/'tools/model_config.json').read_text())
report=dict(status='pass',version=cfg['version'],scope='Final skeleton skinning for inventory and native male/female facegen references; selected facegen idle uses inventory_idle. No engine channel blending, cloth or IK simulation',poses=rows,selected_facegen_idle='inventory_idle',game_verified=False)
(R/'reports/inventory_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('INVENTORY_POSES',[(r['pose'],r['samples'][0]['wrists_torso_bind_m']) for r in rows])
