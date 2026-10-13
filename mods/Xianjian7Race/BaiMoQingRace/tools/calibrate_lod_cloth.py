import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
from refit_skirt_collision import pose_capsule
"""Check actual reduced vertices and change only their cloth alpha bytes."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];WS=workspace_root(R)
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rig=parse_skeljson({'bones':[dict(i=i,**bone) for i,bone in enumerate(json.loads((R/'build/skeleton_spec.json').read_text()))]})
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules'];rows=[]
legacy_caps=json.loads((R/'reports/history/v0.1.0/cloth_collision.json').read_text())['capsules']
cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));allowed={r['object'] for r in json.loads((R/'build/manifest.json').read_text()) if r['material'] in cfg.get('calibrate_materials',[])}
for row in json.loads((R/'build/geometry.json').read_text()):
    if not row.get('cloth'):continue
    blob=bytearray(Path(row['geometry']).read_bytes());_,nv,ni=np.frombuffer(blob,'<i4',3)
    p=np.frombuffer(blob,'<f4',nv*3,12).reshape(nv,3);color_offset=12+nv*56
    colors=np.frombuffer(blob,'u1',nv*4,color_offset).reshape(nv,4)
    bi=np.frombuffer(blob,'u1',nv*4,color_offset+nv*4).reshape(nv,4)
    bw=np.frombuffer(blob,'u1',nv*4,color_offset+nv*8).reshape(nv,4)
    assert len(blob)==12+nv*68+ni*4 and np.all(bw.sum(1)==255) and bi.max()<28
    ids=np.flatnonzero(colors[:,3]>0);assert len(ids)>0 and len(ids)<nv
    rows.append(dict(row=row,blob=blob,p=p,colors=colors,bi=bi,bw=bw,ids=ids,required=np.zeros(len(ids))))
for label in ['idle','run','bow','riding','slash']:
    anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=range(max(1,anim['start']),anim['frames']) if label!='idle' else sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,32).astype(int))|set(np.linspace(max(1,anim['start']),anim['frames']-1,16).astype(int)))
    for frame in frames:
        skin=skin_matrices(rig,anim,frame);posed=[]
        for cap in caps+legacy_caps:
            ab=pose_capsule(cap,skin,rig['names'])
            posed.append((ab,cap['radius_m']))
        for row in rows:
            ids=row['ids'];p=lbs(row['p'][ids],row['bi'][ids],row['bw'][ids],skin)
            for (start,end),radius in (posed[:len(caps)] if row['row']['name'].split('.lod')[0] in allowed else posed[len(caps):]):
                axis=end-start;t=np.clip((p-start)@axis/(axis@axis),0,1)
                row['required']=np.maximum(row['required'],radius-np.linalg.norm(p-start-t[:,None]*axis,axis=1))
source=np.load(R/'build/fitted_model.npz');paint=np.load(R/'build/cloth_alphas.npz');alphas={n:paint[n].copy() for n in paint.files};report=[]
for row in rows:
    ids=row['ids'];before=row['colors'][:,3].copy()
    need=np.ceil(np.clip(row['required']+.004,0,1)*255).astype('u1')
    row['colors'][ids,3]=np.maximum(before[ids],need)
    assert np.array_equal(before==0,row['colors'][:,3]==0)
    Path(row['row']['geometry']).write_bytes(row['blob'])
    report.append(dict(mesh=row['row']['name'],lod=row['row']['lod'],adjusted_vertices=int((row['colors'][:,3]!=before).sum()),fixed_roots_unchanged=True,max_added_travel_m=float((row['colors'][:,3].astype(float)-before).max()/255)))
    if row['row']['lod']==0:
        name=row['row']['name'];dist,near=cKDTree(row['p']).query(source[name+'_p']);assert dist.max()<2e-6
        alphas[name]=row['colors'][near,3].astype('f4')/255
np.savez_compressed(R/'build/cloth_alphas.npz',**alphas)
(R/'reports/cloth_lod_calibration.json').write_text(json.dumps(dict(scope='Actual per-LOD quantized skinning references, all run/bow/riding/slash frames, sampled idle; changes only alpha bytes',rows=report),indent=2))
print('LOD_CLOTH_CALIBRATED',report)
