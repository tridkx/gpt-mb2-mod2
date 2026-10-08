"""Create a sleeve-only recipe from final baseline TPAC geometry."""
from pathlib import Path
import hashlib, json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
config = json.loads((ROOT/'tools/direct_cloth_config.json').read_text())
baseline = BUILD/'sleeve_baseline/tx5.tpac'
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == config['baseline_sha256']
meshes = {m['name']:m for m in json.loads((BUILD/'sleeve_baseline/meshes.json').read_text())}
m = meshes['tx5_body_00']
p = np.array(m['pos'])
f = np.array(m['idx']).reshape(-1,3)
u, inv = np.unique(np.round(p,5), axis=0, return_inverse=True)
edges = np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
we = np.unique(np.sort(inv[edges],axis=1),axis=0)
we = we[we[:,0]!=we[:,1]]
length = np.linalg.norm(u[we[:,0]]-u[we[:,1]],axis=1)
g = coo_matrix((np.r_[length,length],(np.r_[we[:,0],we[:,1]],np.r_[we[:,1],we[:,0]])),shape=(len(u),len(u))).tocsr()
n, labels = connected_components(g)
old = np.array(m['color'])[:,3] / 255.0
effective = np.zeros(len(p))
regions = []
streamer_components = []
for component in range(n):
    ids = np.where(labels[inv]==component)[0]
    q = p[ids]
    if len(ids)<100 or q[:,2].min()>.80 or abs(q[:,0].mean())<.25:
        continue
    # Top strip is the physical attachment; use surface distance, not global Z,
    # so the freedom gradient remains meaningful in the forward-rotated sleeve.
    roots = np.unique(inv[ids[q[:,2] >= q[:,2].max()-config['streamer_root_strip_m']]])
    distance = np.min(dijkstra(g, indices=roots, directed=False),axis=0)[inv[ids]]
    t = np.clip((distance-config['streamer_pin_band_m'])/(config['streamer_transition_m']-config['streamer_pin_band_m']),0,1)
    travel = np.minimum(config['streamer_distance_per_length']*distance,config['streamer_max_distance_m'])*t*t*(3-2*t)
    effective[ids] = travel
    streamer_components.append(component)
    regions.append({'component':component,'vertices':len(ids),'pinned':int((travel==0).sum()),'surface_length_m':float(distance.max()),'max_distance_m':float(travel.max()),'side':'left' if q[:,0].mean()<0 else 'right'})
assert len(regions)==2 and all(r['pinned']>=2 for r in regions)
streamers = np.isin(labels[inv],streamer_components)
# Only the previously designated sleeve edge gains additional freedom. Torso,
# flowers and seam vertices remain fixed; skirt/hair use other submeshes.
edge = (~streamers)&(old>0)
effective[edge] = config['sleeve_edge_max_distance_m']*np.clip(old[edge]/.03,0,1)
multiplier = config['distance_multiplier']
alpha = np.rint(effective/multiplier*255).astype(int)
recipe = {'material':config['material'],'meshes':{},'baseline_sha256':config['baseline_sha256']}
recipe['meshes'][m['name']]={'alpha':alpha.tolist(),'multiplier':multiplier}
lod1=meshes['tx5_body_00.lod1']
# LOD simplification changes vertex positions. Transfer from the nearest accepted
# fabric surface; keep coincident splits consistent with the source distance mask.
dist, nearest = cKDTree(p).query(np.array(lod1['pos']))
assert dist.max()<.055, float(dist.max())
recipe['meshes'][lod1['name']]={'alpha':alpha[nearest].tolist(),'multiplier':multiplier}
(BUILD/'direct_sleeve_mask_recipe.json').write_text(json.dumps(recipe,indent=2))
np.savez_compressed(BUILD/'direct_sleeve_mask.npz',pos=p,alpha=alpha,effective=alpha/255*multiplier,streamers=streamers,edges=edges,labels=labels[inv])
report={'version':config['version'],'route':'direct simulation, LOD0 and LOD1','regions':regions,'sleeve_edge_vertices':int(edge.sum()),'lod1_max_transfer_distance_m':float(dist.max()),'geometry_and_skin_weights_modified':False,'collision_body':'human_body','game_solver_used':False}
(ROOT/'reports/direct_sleeve_preparation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
