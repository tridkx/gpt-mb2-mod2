"""Verify final skirt-only weight repair preserves every rest vertex."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[1];BASE=ROOT/'build/repair_baseline_v1.0.0'
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'));from georead import read_geo
parts=json.loads((ROOT/'reports/rig_fit.json').read_text())['parts'];skirt=next(r['object'] for r in parts if r['kind']=='skirt');old={m['name']:m for f in (BASE/'export/geo').glob('*.bin') for m in read_geo(f)};new={m['name']:m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f)};assert old.keys()==new.keys();unchanged=[]
for name,m in old.items():
    for key in ['pos','uv','idx']:assert np.array_equal(m[key],new[name][key]),(name,key,'rest silhouette changed')
    if name!=skirt:
        for key in ['bi','bw']:assert np.array_equal(m[key],new[name][key]),(name,key,'unrelated weights changed')
        unchanged.append(name)
base=np.load(BASE/'rig_arrays.npz');current=np.load(ROOT/'build/rig_arrays.npz');assert np.array_equal(base[skirt+'_P'],current[skirt+'_P']);assert np.array_equal(base[skirt+'_A'],current[skirt+'_A'])
for lod in range(4):
    folder=ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')/'geo';m=next(m for f in folder.glob('*.bin') for m in read_geo(f) if m['name'].split('.lod')[0]==skirt);assert np.array_equal(m['pos'],new[skirt]['pos']);assert np.array_equal(m['idx'],new[skirt]['idx']);assert np.array_equal(m['bi'],new[skirt]['bi']);assert np.array_equal(m['bw'],new[skirt]['bw'])
cal=json.loads((ROOT/'reports/reference_skirt_calibration.json').read_text());cfg=json.loads((ROOT/'tools/model_config.json').read_text());selected=next(r for r in cal['candidates'] if r['key']==cfg['reference_skirt_candidate']);assert selected['safe_deformation']
release=json.loads((ROOT/'reports/release_validation.json').read_text());assert release['status']=='pass'
for motion in release['motions']:
    predicted=selected['stats'][motion['label']]['depth'];assert abs(motion['skirt_leg_proxy']['deepest_overlap_m']-predicted)<1e-6
    assert predicted<=cal['baseline'][motion['label']]['depth']+.001
package=ROOT/json.loads((ROOT/'mod.json').read_text())['package'];digest=hashlib.sha256(package.read_bytes()).hexdigest()
report={'status':'pass','final_package_sha256':digest,'scope':'preserved accepted rest contour and smooth calf-follow weight repair; offline improvement, game cloth untested','rest_vertex_max_delta_m':0,'leg_geometry_removed':False,'unchanged_lod0_meshes':unchanged,'skirt_cloth_distance_unchanged':True,'all_lods_skirt_geometry_and_weights_identical':True,'candidate':selected,'baseline':cal['baseline'],'reference':'TianxiangRenqiu user-accepted recipe, re-calibrated for this skirt','game_verified':False,'zero_intersections_claimed':False};(ROOT/'reports/reference_skirt_validation.json').write_text(json.dumps(report,indent=2));print('REFERENCE_SKIRT_VERIFIED',ROOT.name)
