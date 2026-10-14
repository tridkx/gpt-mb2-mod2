"""Bounded parallel resource builds; source authoring is a separate Blender phase."""
import json,sys,subprocess,concurrent.futures,time
from pathlib import Path
from context import SERIES
def one(row):
    root=Path(row['root']);log=root/'build/build.log';print('RESOURCE_BEGIN',row['id'],flush=True)
    with log.open('w',encoding='utf8') as out:result=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__).parent/'build_one.py'),str(root)],stdout=out,stderr=subprocess.STDOUT)
    status='pass' if result.returncode==0 else 'error';print('RESOURCE_END',row['id'],status,flush=True);return {'id':row['id'],'status':status,'log':str(log)}
if __name__=='__main__':
    batch=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'));requested=sys.argv[1:];rows=[r for r in batch['characters'] if not requested or r['id'] in requested];results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(one,rows):results.append(result)
    path=SERIES/'batch_resources.json';previous=json.loads(path.read_text()) if path.exists() else [];combined={r['id']:r for r in previous};combined.update({r['id']:r for r in results});path.write_text(json.dumps(list(combined.values()),indent=2));assert all(r['status']=='pass' for r in results),[r['id'] for r in results if r['status']!='pass']
