"""Refresh source manifest and diagnostic scope after final-resource verification."""
import json
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
assert json.loads((R/'reports/release_validation.json').read_text())['status']=='pass'
files=['README.md','CHANGELOG.md','mod.json','.gitignore','.gitattributes']
for directory in ['input','source','tools','reports','module']:
 files.extend(p.relative_to(R).as_posix() for p in (R/directory).rglob('*') if p.is_file() and p.suffix not in ['.log','.blend1','.blend2','.pyc'] and '.fbm' not in str(p) and not any(x in p.parts for x in ['obj','bin','__pycache__','cloth_diagnostics']))
shared=[p.relative_to(W).as_posix() for folder in ['tools/asset_helpers','tools/cloth_compiler','tools/cloth_simulator'] for p in (W/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.cs','.csproj','.md','.html'] and not any(x in p.parts for x in ['obj','bin','__pycache__'])];shared+=['tools/race_action_sets.py']
motions=[{'name':n,'path':f'reports/{n}.json','fps':60,**({'end':61} if n=='facegen' else {})} for n in ['facegen','run','riding']]
target={'skeleton':'reports/final_skeleton.json','capsules':'module/EmilieRace/ModuleData/cloth_bodies.xml','body':'emilie_collision','motions':motions,'settings':{'warmup':30,'substeps':2,'iterations':4}}
config={'id':'EmilieRace','source_files':sorted(set(files)),'shared_source_files':sorted(set(shared)),'package':'module/EmilieRace/AssetPackages/emilie.tpac','validation_report':'reports/release_validation.json','cloth_diagnostics':{'enabled':True,'mode':'report','probe':'build/cloth_probe/NativeClothProbe.dll','targets':[dict(target,metamesh='emilie_body',lods=[0,1,2,3]),dict(target,metamesh='emilie_cloth_proxy',lods=[0])]}}
(R/'mod.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8')
if not (R/'reports/game_acceptance.json').exists():(R/'reports/game_acceptance.json').write_text(json.dumps({'version':'v0.1.0','status':'pending_user_test','game_launched_by_assistant':False,'required_scenes':['party','encyclopedia','inventory','idle','run','bow','slash','riding','cloth_lod_distances'],'cloth_scope':['hat_trail','back_ribbons'],'skirt_cloth_enabled':False},indent=2))
config['source_files']=sorted(set(config['source_files']+['reports/game_acceptance.json']));(R/'mod.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf8');print('DELIVERY_MANIFEST_READY',len(files))
