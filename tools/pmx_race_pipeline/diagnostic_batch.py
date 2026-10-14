"""Diagnose completed final previews while the remaining models render."""
import concurrent.futures,json,time
from pathlib import Path
from context import SERIES
from collection import diagnostic
rows=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'))['characters']
pending={r['id']:Path(r['root']) for r in rows};jobs={};results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    while pending or jobs:
        log=(SERIES/'final_preview.log').read_text(encoding='utf8',errors='replace')
        for identity in list(pending):
            if 'FINAL_PREVIEW_DONE '+identity in log:
                jobs[pool.submit(diagnostic,pending.pop(identity))]=identity
        for job in list(jobs):
            if job.done():
                identity=jobs.pop(job)
                try:result=job.result();results.append(result);print('DIAGNOSTIC_DONE',identity,result['status'],flush=True)
                except Exception as error:results.append({'id':identity,'status':'error','error':str(error)});print('DIAGNOSTIC_ERROR',identity,str(error),flush=True)
        if 'Blender quit' in log and pending:raise RuntimeError('Final previews ended before all models were ready: '+str(list(pending)))
        if pending or jobs:time.sleep(5)
(SERIES/'batch_diagnostics.json').write_text(json.dumps(results,indent=2))
assert all(r['status']!='error' for r in results)
