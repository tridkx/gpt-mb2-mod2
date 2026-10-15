"""Render final package previews sequentially; keep simulation proxies off screen."""
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import SERIES,execute,config
batch=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'));requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];results=[]
for row in batch['characters']:
    if requested and row['id'] not in requested:continue
    root=Path(row['root']);c=config(root)
    report=root/'reports/release_validation.json'
    if not report.exists() or json.loads(report.read_text()).get('status')!='pass':continue
    try:
        print('FINAL_PREVIEW_BEGIN',c['id'],flush=True);sys.argv=[sys.argv[0],'--','0','--review'];execute('render_final',root)
        # Distant LOD silhouette/face is also inspected from final bytes.
        sys.argv=[sys.argv[0],'--','3','--rest'];execute('render_final',root)
        if c['cloth_enabled'] and c.get('cloth_mode')!='direct':execute('save_proxy_source',root)
        results.append({'id':c['id'],'status':'pass'});print('FINAL_PREVIEW_DONE',c['id'],flush=True)
    except Exception:
        error=traceback.format_exc();print(error,flush=True);(root/'reports/preview_failure.txt').write_text(error);results.append({'id':c['id'],'status':'error'})
path=SERIES/'batch_previews.json';previous=json.loads(path.read_text()) if path.exists() else [];combined={r['id']:r for r in previous};combined.update({r['id']:r for r in results});path.write_text(json.dumps(list(combined.values()),indent=2));assert all(r['status']=='pass' for r in results)
