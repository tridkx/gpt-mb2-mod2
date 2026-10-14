"""Collect editable and reconstruction files without caches or prior packages."""
from pathlib import Path
import json
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);cfg=json.loads((R/'mod.json').read_text());files=[]
for folder in ['input','source','tools','reports']:
 for p in (R/folder).rglob('*'):
  if p.is_file() and not any(part in {'obj','bin','__pycache__'} for part in p.relative_to(R).parts) and p.suffix not in {'.pyc','.blend1','.blend2'}:files.append(p.relative_to(R).as_posix())
cfg['source_files']=sorted(set(files+['README.md','CHANGELOG.md','mod.json']))
cfg['shared_source_files']=[p.relative_to(W).as_posix() for folder in ['tools/asset_helpers','tools/cloth_compiler','tools/cloth_simulator'] for p in (W/folder).rglob('*') if p.is_file() and p.suffix in {'.py','.cs','.csproj','.html','.md'} and not any(x in {'__pycache__','obj','bin','reports'} for x in p.relative_to(W/folder).parts)]+['tools/race_action_sets.py']
(R/'mod.json').write_text(json.dumps(cfg,indent=2)+'\n');print('SOURCE_MANIFEST_READY',len(cfg['source_files']))
