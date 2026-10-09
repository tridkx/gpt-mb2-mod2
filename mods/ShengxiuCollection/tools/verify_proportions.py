"""Cloth-only revision preserves the accepted v1.0.1 geometry and skin."""
from pathlib import Path
import numpy as np,json,hashlib,sys
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'))
from georead import read_geo
base=ROOT/'build/cloth_baseline_v1.0.2'
old=np.load(base/'rig_arrays.npz');new=np.load(ROOT/'build/rig_arrays.npz')
assert np.array_equal(old['world'],new['world'])
records=json.loads((ROOT/'build/rig_manifest.json').read_text())
for rec in records:
 n=rec['object']
 for field in ['S','P','W']:assert np.array_equal(old[n+'_'+field],new[n+'_'+field]),(n,field)
 assert np.array_equal(old[n+'_A'],new[n+'_A'])
for file in (ROOT/'build/final_export/geo').glob('*.bin'):
 for mesh in read_geo(file):assert cKDTree(new[mesh['name']+'_P']).query(mesh['pos'])[0].max()<2e-6
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
previous=json.loads((base/'proportion_validation.json').read_text())
report={'status':'pass','version':'v1.0.3','final_package_sha256':sha(ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'),
 'baseline_package_sha256':sha(base/'sx_mingyu.tpac'),'all_bind_geometry_exactly_preserved':True,
 'all_weights_exactly_preserved':True,'native_skeleton_unchanged':True,
 'preserved_v1_0_1_measurements':previous['preserved_v1_0_1_measurements'],
 'all_cloth_alpha_preserved':True,'intentional_changes':'force_enable_cloth and observed native UnknownBool3 only','game_test_verified':False}
(ROOT/'reports/proportion_validation.json').write_text(json.dumps(report,indent=2))
print('ACCEPTED_HEAD_NECK_FEET_AND_ALL_GEOMETRY_PRESERVED')
