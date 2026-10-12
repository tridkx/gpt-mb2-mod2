import json,sys,numpy as np
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));inverse=np.linalg.inv(rig['restWorld'])
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules'];names=rig['names']
mesh=next(json.loads(p.read_text()) for p in (R/'build/cloth_final').glob('*.mesh.json') if json.loads(p.read_text())['lod']==0)
pos=np.array(mesh['positions']);fixed=np.array(mesh['alpha'])==0
plans=json.loads((R/'build/cooked_cloth/manifest.json').read_text());plan=next(p for p in plans if p['guid']==mesh['guid']);fixed[plan['solver_pinned_render_vertices']]=True
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
source=np.load(R/'build/source_samples.npz');original=source['mesh_12_947881_p'];tri=source['mesh_12_947881_f']
edges=np.vstack([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(original),len(original))),directed=False)
_,nearest=cKDTree(original).query(pos);sizes=np.bincount(labels);major=sizes[labels[nearest]]>150
rows=[]
for label in ['rest','ui_neutral_male','run','bow','riding']:
    anim=None if label=='rest' else parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=[0] if anim is None else sorted(set(np.linspace(anim['start'],anim['frames']-1,16).astype(int)))
    worst={}
    for frame in frames:
        world=rig['restWorld'].copy()
        if anim is not None:
            for i,parent in enumerate(rig['parent']):
                local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame])
                if parent<0:local[:3,3]+=anim['rootPos'][frame]
                world[i]=local if parent<0 else world[parent]@local
        skin=world@inverse;p=lbs(pos,np.array(mesh['bones']),np.array(mesh['weights']),skin)
        overlap=np.zeros(len(p))
        for c in caps:
            endpoints=[]
            for point,bone in zip(c['endpoints_m'],c['bones']):
                i=names.index(bone);endpoints.append(skin[i,:3,:3]@point+skin[i,:3,3])
            a,b=endpoints;v=b-a;t=np.clip((p-a)@v/(v@v),0,1)
            overlap=np.maximum(overlap,c['radius_m']-np.linalg.norm(p-a-t[:,None]*v,axis=1))
        for bucket,lo,hi in [('main_long_roots',.1,.9),('waist',.83,1),('long_root',.74,.83),('ornaments',0,.74)]:
            ids=np.flatnonzero(fixed&(pos[:,2]>lo)&(pos[:,2]<=hi)&(major if bucket=='main_long_roots' else ~major))
            if not len(ids):continue
            i=ids[np.argmax(overlap[ids])]
            if overlap[i]>worst.get(bucket,{}).get('overlap_m',-1):worst[bucket]=dict(frame=int(frame),overlap_m=float(overlap[i]),source_point=pos[i].tolist(),index=int(i))
    rows.append(dict(pose=label,buckets=worst))
(R/'reports/root_conflict_diagnostic.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
