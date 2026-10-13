"""Compare preserved PSK coordinates with source arrays and final TPAC LOD0."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import psk_lib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
cfg=json.loads((R/'tools/model_config.json').read_text());p=psk_lib.check(psk_lib.read(R/'input/SK_BR_nofoot.psk'));points=p['points']@np.array(cfg['source_rotation']).T*cfg['source_scale']
a=np.load(R/'build/fitted_model.npz');manifest=json.loads((R/'build/manifest.json').read_text());meshes=[m for f in (R/'build/final_export_lod0/geo').glob('*.bin') for m in read_geo(f) if not m['name'].startswith('boru_race_hidden')];rows=[]
for rec in manifest:
    n=rec['object'];src=points[a[n+'_source_ids']];err=float(abs(src-a[n+'_p']).max());assert err<1e-6
    groups=[m for m in meshes if m['name'].split('.b')[0]==n];q=np.concatenate([m['pos'] for m in groups]);error=float(cKDTree(q).query(src)[0].max());assert error<2e-6,(n,error)
    u=np.concatenate([m['uv'] for m in groups]);u[:,1]=1-u[:,1]
    expected=np.concatenate([a[n+'_p'],a[n+'_uv']],1);actual=np.concatenate([q,u],1)
    uv_error=float(cKDTree(expected).query(actual)[0].max());assert uv_error<2e-6,(n,'UV',uv_error)
    rows.append(dict(part=n,source_error_m=err,final_lod0_error_m=error,position_uv_error=uv_error))
tri=p['wedges']['pt'][np.stack([p['faces']['w0'],p['faces']['w1'],p['faces']['w2']],1)]
area=np.linalg.norm(np.cross(points[tri[:,1]]-points[tri[:,0]],points[tri[:,2]]-points[tri[:,0]]),axis=1)/2
assert sum(m['nidx']//3 for m in meshes)==int((area>=1e-16).sum())
(R/'reports/preservation_validation.json').write_text(json.dumps(dict(status='pass',uniform_scale=cfg['source_scale'],rotation=cfg['source_rotation'],anatomy_warp=False,source_triangles=len(p['faces']),parts=rows,uv_exception='Eye UV projected to supplied iris disc; all other UV retained'),indent=2))
print('PROPORTIONS_PRESERVED',rows)
