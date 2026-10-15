"""Run inside background Blender, independently preserving every character source."""
from pathlib import Path
import sys,json
S=Path(__file__).resolve().parents[1];W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir());sys.path.insert(0,str(W/'tools/pmx_race_pipeline'))
from context import execute
from source_preview import preview
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for row in json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters']:
 if selected and row['id'] not in selected:continue
 root=S/row['id'];print('SOURCE_BEGIN',root.name,flush=True)
 for stage in ['create_source','export_geometry','verify_source']:execute(stage,root)
 preview(root);print('SOURCE_DONE',root.name,flush=True)
