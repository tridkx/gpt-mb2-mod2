"""Render final TPAC bytes and quantified native poses for every delivered LOD."""
from pathlib import Path
import sys,json
S=Path(__file__).resolve().parents[1];W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir());sys.path.insert(0,str(W/'tools/pmx_race_pipeline'))
from context import execute
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for row in json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters']:
 if selected and row['id'] not in selected:continue
 root=S/row['id'];assert (root/'reports/release_validation.json').exists()
 for lod in range(4):
  sys.argv=['render','--',str(lod)];execute('render_final',root)
 print('FINAL_PREVIEW_DONE',root.name,flush=True)
