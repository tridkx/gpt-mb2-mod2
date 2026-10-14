"""Build and inspect selected source projects sequentially in one Blender process."""
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import SERIES,execute
from source_preview import preview
batch=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'));requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];results=[]
for row in batch['characters']:
    root=Path(row['root'])
    if requested and row['id'] not in requested:continue
    try:
        print('SOURCE_BEGIN',row['id'],flush=True);execute('create_source',root);execute('export_geometry',root);execute('verify_source',root);preview(root);results.append({'id':row['id'],'status':'pass'})
        failure=root/'reports/source_failure.txt'
        if failure.exists():failure.unlink()
    except Exception:
        error=traceback.format_exc();print(error,flush=True);(root/'reports/source_failure.txt').write_text(error,encoding='utf8');results.append({'id':row['id'],'status':'error','error':error})
path=SERIES/'batch_source_build.json';previous=json.loads(path.read_text()) if path.exists() else [];combined={r['id']:r for r in previous};combined.update({r['id']:r for r in results});path.write_text(json.dumps(list(combined.values()),indent=2));assert all(r['status']=='pass' for r in results),[r['id'] for r in results if r['status']!='pass']
