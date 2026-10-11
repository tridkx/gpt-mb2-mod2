"""Update source manifest and attest to the exact module files checked offline."""
import json,hashlib,sys
import numpy as np
from scipy.spatial import cKDTree
from pathlib import Path
R=Path(__file__).resolve().parents[1]
W=next(p for p in R.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(W/'tools/asset_helpers/tools'))
from georead import read_geo
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((R/'reports/release_validation.json').read_text());assert report['status']=='pass'
package=R/'module/TianxiangT5PVERace/AssetPackages/txt5pve.tpac'
assert sha(package)==report['final_package_sha256']
arrays=np.load(R/'build/fitted_model.npz');errors=[]
for path in (R/'build/final_export_lod0/geo').glob('*.bin'):
    for mesh in read_geo(path):
        if mesh['name'].startswith('txt5pve_hidden'):continue
        name=mesh['name'].split('.b')[0];distance,_=cKDTree(arrays[name+'_p']).query(mesh['pos']);error=float(distance.max());assert error<2e-6
        errors.append({'mesh':name,'source_distance_max_m':error})
materials=json.loads((R/'tex/materials.json').read_text())
assert materials['tunic_D-PVE']['diffuse']=='tunic_D-PVE.png' and materials['pants_D-PVE']['diffuse']=='pants_D-PVE.png'
assert all('-PVP' not in info['diffuse'] for info in materials.values())
report.update(date='2026-10-11',final_lod0_source_geometry=errors,pve_texture_sha256={info['diffuse']:sha(R/'tex'/info['diffuse']) for info in materials.values()})
source=json.loads((R/'reports/source_validation.json').read_text());assert source['status']=='pass'
preview=json.loads((R/'reports/final_preview_manifest.json').read_text());assert preview['package_sha256']==sha(package)
dll=R/'module/TianxiangT5PVERace/bin/Win64_Shipping_Client/TianxiangT5PVERace.UIRuntime.dll';assert dll.is_file()
actions=(R/'module/TianxiangT5PVERace/ModuleData/action_sets.xml').read_text()
assert all('as_txt5pve_'+suffix in actions for suffix in ['warrior','female_warrior','facegen','female_facegen'])
runtime=(R/'tools/UIRuntime/Runtime.cs').read_text()
assert all(token in runtime for token in ['races[data.RaceData]!="txt5pve"','oldSkeleton.GetName()=="txt5pve_skeleton"','typeof(Equipment)','false,true,null,false,false','ApplyScaleLocal(1f/scale)','MissionScreen'])
report.update(source_validation=source,ui_runtime={'status':'compiled_and_offline_scope_checked','assembly_sha256':sha(dll),'target_race':'txt5pve','target_skeleton':'txt5pve_skeleton','game_verified':False})
report['module_file_sha256']={p.relative_to(R/'module/TianxiangT5PVERace').as_posix():sha(p) for p in (R/'module/TianxiangT5PVERace').rglob('*') if p.is_file()}
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
files=[p.relative_to(R).as_posix() for directory in ['input','source','tools','reports'] for p in (R/directory).rglob('*') if p.is_file() and not any(x in p.parts for x in ['obj','bin','__pycache__']) and p.suffix not in ['.pyc','.log','.blend1']]
files+=['README.md','CHANGELOG.md','.gitignore','.gitattributes','mod.json']
shared=['tools/asset_helpers/'+x for x in ['config/spec.py','pipeline/build_assets.py','pipeline/convert_textures.py','pipeline/paths.py','previewer/baker/__init__.py','previewer/baker/animation.py','previewer/baker/config.py','previewer/baker/skeleton.py','tools/georead.py']]
(R/'mod.json').write_text(json.dumps({'id':'TianxiangT5PVERace','source_files':sorted(files),'shared_source_files':shared,'package':'module/TianxiangT5PVERace/AssetPackages/txt5pve.tpac','validation_report':'reports/release_validation.json'},indent=2))
print('RELEASE_READY',report['version'],report['final_package_sha256'])
