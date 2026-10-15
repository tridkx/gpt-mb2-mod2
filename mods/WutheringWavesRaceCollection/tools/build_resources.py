"""Build only the requested independent modules from verified source geometry."""
from pathlib import Path
import sys,json,concurrent.futures,subprocess
S=Path(__file__).resolve().parents[1];W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir())
def build(row):
 root=S/row['id'];assert (root/'reports/source_validation.json').is_file()
 log=root/'build/resource.log'
 with log.open('w',encoding='utf8') as out:
  args=[sys.executable,'-B','-X','utf8',str(W/'tools/pmx_race_pipeline/build_one.py'),str(root)]
  if (root/'build/spec.json').is_file():args.append('--reuse-textures')
  result=subprocess.run(args,stdout=out,stderr=subprocess.STDOUT)
 print('RESOURCE_DONE',root.name,result.returncode,flush=True)
 if result.returncode:raise RuntimeError(log.read_text(encoding='utf8',errors='replace')[-5000:])
 return {'id':root.name,'status':'pass'}
if __name__=='__main__':
 requested=sys.argv[1:];rows=[r for r in json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters'] if not requested or r['id'] in requested]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(build,rows))
 (S/'reports').mkdir(exist_ok=True);(S/'reports/resource_build.json').write_text(json.dumps(results,indent=2))
