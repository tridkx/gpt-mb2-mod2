import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
from refit_skirt_collision import pose_capsule
"""Increase only active travel where source-sized animated capsules require it."""
import json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];WS=workspace_root(R)
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rig=parse_skeljson({'bones':[dict(i=i,**bone) for i,bone in enumerate(json.loads((R/'build/skeleton_spec.json').read_text()))]})
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules']
legacy_caps=json.loads((R/'reports/history/v0.1.0/cloth_collision.json').read_text())['capsules']
source=np.load(R/'build/fitted_model.npz');old=np.load(R/'build/cloth_alphas.npz');result={name:old[name].copy() for name in old.files};needs={name:np.zeros(len(old[name])) for name in old.files}
cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));allowed={r['object'] for r in json.loads((R/'build/manifest.json').read_text()) if r['material'] in cfg.get('calibrate_materials',[])}
for label in ['run','idle','bow','riding','slash']:
    anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=range(anim['start'],anim['frames']) if label=='run' else sorted(set(np.linspace(anim['start'],anim['frames']-1,24).astype(int)))
    for frame in frames:
        skin=skin_matrices(rig,anim,frame);posed=[]
        for cap in caps+legacy_caps:
            ab=pose_capsule(cap,skin,rig['names'])
            posed.append((ab,cap['radius_m']))
        for name,a in result.items():
            ids=np.flatnonzero(old[name]>0)
            if not len(ids):continue
            w=source[name+'_w'][ids];bi=np.argsort(-w,axis=1)[:,:4];weights=np.take_along_axis(w,bi,axis=1)
            q=np.floor(weights*255).astype(int);q[:,0]+=255-q.sum(1)
            p=lbs(source[name+'_p'][ids],bi,q,skin);required=np.zeros(len(ids))
            for (start,end),radius in (posed[:len(caps)] if name in allowed else posed[len(caps):]):
                axis=end-start;t=np.clip((p-start)@axis/(axis@axis),0,1)
                required=np.maximum(required,radius-np.linalg.norm(p-start-t[:,None]*axis,axis=1))
            needs[name][ids]=np.maximum(needs[name][ids],required)
rows=[]
for name,a in result.items():
    active=old[name]>0;a[active]=np.maximum(a[active],needs[name][active]+.004)
    assert np.array_equal(a==0,old[name]==0)
    rows.append(dict(object=name,adjusted_vertices=int((a>old[name]+1e-6).sum()),max_added_travel_m=float((a-old[name]).max()),fixed_roots_unchanged=True,max_travel_m=float(a.max())))
np.savez_compressed(R/'build/cloth_alphas.npz',**result)
(R/'reports/cloth_travel_calibration.json').write_text(json.dumps(dict(scope='Source skinning references and animated capsule clearance, not engine cloth simulation',rows=rows),indent=2))
print('TRAVEL_CALIBRATED',rows)
