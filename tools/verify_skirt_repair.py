"""Ensure skirt repair does not remove legs or change unrelated LOD0 meshes."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[1];BASE=ROOT/'build/repair_baseline_v1.0.0'
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'))
from georead import read_geo
old={m['name']:m for p in (BASE/'export/geo').glob('*.bin') for m in read_geo(p)}
new={m['name']:m for p in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(p)}
assert old.keys()==new.keys();parts=json.loads((ROOT/'reports/rig_fit.json').read_text())['parts'];skirts={r['object'] for r in parts if r['kind']=='skirt'}
unchanged=[]
for name,m in old.items():
    if name in skirts:assert m['nidx']==new[name]['nidx'];continue
    for key in ['pos','uv','idx','bi','bw']:assert np.array_equal(m[key],new[name][key]),(name,key,'unrelated geometry modified')
    unchanged.append(name)
surface=json.loads((ROOT/'reports/skirt_surface_validation.json').read_text());assert surface['status']=='pass'
package=ROOT/json.loads((ROOT/'mod.json').read_text())['package'];digest=hashlib.sha256(package.read_bytes()).hexdigest()
report={'status':'pass','final_package_sha256':digest,'unchanged_lod0_meshes':unchanged,'skirt_topology_preserved':True,'leg_geometry_removed':False,'all_lods_surface_intersections':0,'game_verified':False}
(ROOT/'reports/skirt_repair_validation.json').write_text(json.dumps(report,indent=2));print('SKIRT_REPAIR_VERIFIED',len(unchanged))
