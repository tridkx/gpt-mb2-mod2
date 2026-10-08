"""Prepare independent direct fabric segments from immutable accepted geometry."""
from pathlib import Path
import json, hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from cloth_format import cook, read_cook, write_cook
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/direct_cloth';OUT.mkdir(exist_ok=True)
config=json.loads((ROOT/'tools/direct_cloth_config.json').read_text())
base={m['name']:m for m in json.loads((ROOT/'build/sleeve_baseline/meshes.json').read_text())}
mask=json.loads((ROOT/'build/direct_sleeve_mask_recipe.json').read_text())
recipe={'version':config['version'],'baseline_sha256':config['baseline_sha256'],'meshes':{}}
reports=[]
for name in ['tx5_body_00','tx5_body_00.lod1','tx5_body_03','tx5_head_01']:
    m=base[name];p=np.array(m['pos']);normal=np.array(m['normal']);bi=np.array(m['bi']);bw=np.array(m['bw'])
    faces=np.array(m['idx']).reshape(-1,3)
    settings=mask['meshes'].get(name)
    a=np.array(settings['alpha'] if settings else [c[3] for c in m['color']],dtype=int)
    multiplier=config['distance_multiplier'] if settings else m['multiplier']
    material=config['material'] if settings else m['cloth']
    # Weld export seams only when the skin influences also agree. Keep different
    # skin anchors separate even if their bind positions coincide.
    key=np.column_stack([np.round(p,5),bi,bw])
    _,reps,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
    wp=p[reps];wa=np.full(len(reps),255,dtype=int);np.minimum.at(wa,inv,a)
    wn=np.zeros_like(wp);np.add.at(wn,inv,normal)
    wn/=np.maximum(np.linalg.norm(wn,axis=1,keepdims=True),1e-12)
    wf=inv[faces];wf=wf[np.array([len(set(tri))==3 for tri in wf])]
    wf=np.unique(wf,axis=0)
    edges=np.unique(np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1),axis=0)
    g=coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(wp),len(wp)))
    count,labels=connected_components(g)
    pinned_islands=[]
    for k in range(count):
        ids=np.flatnonzero(labels==k)
        if np.any(wa[ids]>0) and not np.any(wa[ids]==0):
            # An unattached ornament must keep its own skin anchor. Never tether
            # it to an unrelated sleeve or the opposite side of the garment.
            pinned_islands.append({'particles':len(ids),'vertices':int(np.isin(inv,ids).sum())})
            wa[ids]=0
    a=wa[inv]
    data,reorder,_,_=cook(wp,wn,wf,wa/255,bi[reps],bw[reps]/255)
    c=read_cook(data)
    # The native segment stores one entry per render vertex, allowing many UV
    # splits to share a simulation particle. Other arrays stay particle-sized.
    c['render_to_particle']=reorder[inv]
    data=write_cook(c);path=OUT/(name+'.cooked.bin');path.write_bytes(data)
    recipe['meshes'][name]={'alpha':a.tolist(),'multiplier':multiplier,'material':material,'cooked':str(path.resolve()),'position_representatives':reps.tolist(),'vertex_to_position':inv.tolist()}
    reports.append({'mesh':name,'render_vertices':len(p),'particles':len(wp),'active_particles':int((wa>0).sum()),'fixed_particles':c['header'][3],'constraints':len(c['pairs']),'pinned_unattached_islands':pinned_islands,'max_distance_m':float(a.max()/255*multiplier)})
(OUT/'recipe.json').write_text(json.dumps(recipe,indent=2))
report={'version':config['version'],'baseline_package_sha256':config['baseline_sha256'],'route':'independent direct simulation; no external proxy or render mappings','meshes':reports,'game_solver_used':False}
(ROOT/'reports/direct_cloth_preparation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
