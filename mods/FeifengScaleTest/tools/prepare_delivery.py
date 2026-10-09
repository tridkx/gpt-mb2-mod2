import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];WS=R.parents[1]
files=[]
for directory in ['input','source','tools','reports']:
 for path in (R/directory).rglob('*'):
  if not path.is_file() or path.name=='.gitkeep' or path.suffix in {'.blend1','.pyc'} or any(p in {'obj','bin','__pycache__'} for p in path.relative_to(R/directory).parts):continue
  files.append(path.relative_to(R).as_posix())
shared=[]
for base in [WS/'tools/asset_helpers',WS/'tools/AssetTool']:
 for path in base.rglob('*'):
  if path.is_file() and path.suffix in {'.py','.cs','.csproj','.md','.json'} and not any(p in {'obj','bin','__pycache__'} for p in path.relative_to(base).parts):shared.append(path.relative_to(WS).as_posix())
configuration=dict(id='FeifengScaleTest',version='v0.1.0',source_files=['README.md','CHANGELOG.md','mod.json','.gitignore','.gitattributes']+sorted(files),shared_source_files=sorted(shared),package='module/FeifengScaleTest/AssetPackages/ffs.tpac',validation_report='reports/release_validation.json')
(R/'mod.json').write_text(json.dumps(configuration,indent=2,ensure_ascii=False));print('DELIVERY_CONFIGURED',len(files),'mod files')
