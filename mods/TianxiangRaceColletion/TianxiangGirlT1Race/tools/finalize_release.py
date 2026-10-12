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
package=R/'module/TianxiangGirlT1Race/AssetPackages/txgirl1.tpac'
assert sha(package)==report['final_package_sha256']
arrays=np.load(R/'build/fitted_model.npz');errors=[]
for path in (R/'build/final_export_lod0/geo').glob('*.bin'):
    for mesh in read_geo(path):
        if mesh['name'].startswith('txgirl1_hidden'):continue
        name=mesh['name'].split('.b')[0];distance,_=cKDTree(arrays[name+'_p']).query(mesh['pos']);error=float(distance.max());assert error<2e-6
        errors.append({'mesh':name,'source_distance_max_m':error})
materials=json.loads((R/'tex/materials.json').read_text())
assert materials['tunic_D']['diffuse']=='tunic_D.png' and materials['pants_D']['diffuse']=='pants_D.png'
assert all('-PVP' not in info['diffuse'] for info in materials.values())
report.update(date='2026-10-12',final_lod0_source_geometry=errors,source_texture_sha256={info['diffuse']:sha(R/'tex'/info['diffuse']) for info in materials.values()})
source=json.loads((R/'reports/source_validation.json').read_text());assert source['status']=='pass'
preview=json.loads((R/'reports/final_preview_manifest.json').read_text());assert preview['package_sha256']==sha(package)
dll=R/'module/TianxiangGirlT1Race/bin/Win64_Shipping_Client/TianxiangGirlT1Race.UIRuntime.dll';assert dll.is_file()
actions=(R/'module/TianxiangGirlT1Race/ModuleData/action_sets.xml').read_text()
assert all('as_txgirl1_'+suffix in actions for suffix in ['warrior','female_warrior','facegen','female_facegen'])
runtime=(R/'tools/UIRuntime/Runtime.cs').read_text()
assert all(token in runtime for token in ['races[data.RaceData]!="txgirl1"','oldSkeleton.GetName()=="txgirl1_skeleton"','typeof(Equipment)','false,true,null,false,false','ApplyScaleLocal(1f/scale)','MissionScreen'])
report.update(source_validation=source,ui_runtime={'status':'compiled_and_offline_scope_checked','assembly_sha256':sha(dll),'target_race':'txgirl1','target_skeleton':'txgirl1_skeleton','game_verified':False})
cloth=json.loads((R/'reports/cloth_validation.json').read_text());assert cloth['status']=='pass' and cloth['final_package_sha256']==sha(package)
report['cloth_validation']=cloth
ui_scope=json.loads((R/'reports/ui_scope_validation.json').read_text());assert ui_scope['status']=='pass' and ui_scope['assembly_sha256']==sha(dll)
report['ui_scope_validation']=ui_scope
for filename in ['preview_idle_validation','shorts_collision_validation']:
    file=R/'reports'/(filename+'.json')
    if file.exists():
        check=json.loads(file.read_text())
        assert check['version']==report['version'] and check['status'].startswith('pass')
        report[filename]=check
arm=R/'reports/arm_binding_validation.json'
if arm.exists():
    validation=json.loads(arm.read_text())
    assert validation['status']=='pass' and validation['package_sha256']==sha(package)
    report['arm_binding_validation']=validation
revision=R/'reports/fit_revision_validation.json'
if revision.exists():
    fit=json.loads(revision.read_text())
    if fit['version']==report['version']:
        assert fit['status']=='pass' and fit['ui_dll_sha256']==sha(dll)
        report['fit_revision_validation']=fit
report['module_file_sha256']={p.relative_to(R/'module/TianxiangGirlT1Race').as_posix():sha(p) for p in (R/'module/TianxiangGirlT1Race').rglob('*') if p.is_file()}
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
files=[p.relative_to(R).as_posix() for directory in ['input','source','tools','reports'] for p in (R/directory).rglob('*') if p.is_file() and not any(x in p.parts for x in ['obj','bin','__pycache__']) and p.suffix not in ['.pyc','.log','.blend1']]
files+=['README.md','CHANGELOG.md','.gitignore','.gitattributes','mod.json']
# Retain the exact user-tested UI binary for isolated resource rebuilds.
files+=['module/TianxiangGirlT1Race/bin/Win64_Shipping_Client/TianxiangGirlT1Race.UIRuntime.dll']
shared=['tools/asset_helpers/'+x for x in ['config/spec.py','pipeline/build_assets.py','pipeline/convert_textures.py','pipeline/paths.py','previewer/baker/__init__.py','previewer/baker/animation.py','previewer/baker/config.py','previewer/baker/skeleton.py','tools/georead.py']]
shared+=['tools/cloth_compiler/'+x for x in ['README.md','cloth_payload.py','cook_cloth.py','validation.py','NativeClothProbe.cs','NativeClothProbe.csproj','ClothPatch.cs','ClothPatch.csproj']]
(R/'mod.json').write_text(json.dumps({'id':'TianxiangGirlT1Race','source_files':sorted(files),'shared_source_files':shared,'package':'module/TianxiangGirlT1Race/AssetPackages/txgirl1.tpac','validation_report':'reports/release_validation.json'},indent=2))
print('RELEASE_READY',report['version'],report['final_package_sha256'])
