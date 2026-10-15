"""Verify, diagnose, install independent modules; assemble a management ZIP."""
from pathlib import Path
import sys,json,subprocess,hashlib,zipfile,concurrent.futures,shutil
S=Path(__file__).resolve().parents[1];W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir());sys.path.insert(0,str(W/'tools'));sys.path.insert(0,str(S/'tools'))
from finalize import finalize
from cloth_simulator.pipeline import ensure_diagnostics,delivery_files
GAME=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def deliver(row):
 root=S/row['id'];ident=root.name
 existing=root/'reports/delivery_validation.json'
 if existing.exists():
  cfg=json.loads((root/'mod.json').read_text(encoding='utf8'))
  previous=json.loads(existing.read_text());module=root/'module'/ident
  assert previous['status']=='pass' and previous['final_package_sha256']==sha(root/cfg['package'])
  assert all(p.read_bytes()==(GAME/ident/p.relative_to(module)).read_bytes() for p in module.rglob('*') if p.is_file())
  print('INSTALLATION_REVERIFIED',ident,flush=True);return previous
 if not (root/'mod.json').exists():finalize(root)
 cfg=json.loads((root/'mod.json').read_text(encoding='utf8'))
 print('DIAGNOSTIC_BEGIN',ident,flush=True);result=ensure_diagnostics(root,cfg);print('DIAGNOSTIC_DONE',ident,result['status'],flush=True)
 assert result['status']!='error'
 log=root/'build/install.log'
 with log.open('w',encoding='utf8') as out:
  shell=shutil.which('pwsh');assert shell,'PowerShell 7 is required for the shared installer'
  p=subprocess.run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/install_release.ps1'),'-Mod',ident,'-Version','v0.1.0'],stdout=out,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(log.read_text(encoding='utf8',errors='replace')[-4000:])
 module=root/'module'/ident
 with zipfile.ZipFile(root/'dist'/(ident+'_Mod.zip')) as z:
  files=[p for p in module.rglob('*') if p.is_file()];assert all(p.read_bytes()==(GAME/ident/p.relative_to(module)).read_bytes()==z.read(ident+'/'+p.relative_to(module).as_posix()) for p in files)
 report={'id':ident,'version':'v0.1.0','date':'2026-10-15','status':'pass','installed_module':str(GAME/ident),'installed_files':len(files),'final_package_sha256':sha(root/cfg['package']),'cloth_diagnostic_status':result['status'],'game_launched':False}
 (root/'reports/delivery_validation.json').write_text(json.dumps(report,indent=2));print('INSTALLED',ident,flush=True);return report
def assemble(rows):
 (S/'dist').mkdir(exist_ok=True);modzip=S/'dist/WutheringWavesRaceCollection_v0.1.0_Mod.zip';sourcezip=S/'dist/WutheringWavesRaceCollection_v0.1.0_Source.zip'
 assert not sourcezip.exists(),'Preserve existing release archives; use a new version'
 files={};source={};validation=[]
 for row in rows:
  root=S/row['id'];ident=root.name;cfg=json.loads((root/'mod.json').read_text(encoding='utf8'));r=json.loads((root/'reports/delivery_validation.json').read_text());assert r['status']=='pass';validation.append(r)
  module=root/'module'/ident
  for p in module.rglob('*'):
   if p.is_file():files[ident+'/'+p.relative_to(module).as_posix()]=p
  for p in [root/q for q in cfg['source_files']]+[p for p in (root/'tex').rglob('*') if p.is_file()]:source[ident+'/'+p.relative_to(root).as_posix()]=p
  for p in (root/'reports').glob('*'):
   if p.is_file() and p.suffix in ['.jpg','.png','.json']:source[ident+'/'+p.relative_to(root).as_posix()]=p
  for q in cfg['shared_source_files']:
   p=W/q;source['workspace_tools/'+p.relative_to(W/'tools').as_posix()]=p
  extra,shared=delivery_files(root,json.loads((root/'reports/cloth_diagnostics.json').read_text()))
  for p,entry in extra:source[ident+'/'+entry]=p
  for p,entry in shared:source[entry]=p
  for p in module.rglob('*'):
   if p.is_file():source[ident+'/module/'+ident+'/'+p.relative_to(module).as_posix()]=p
 for p in [S/'README.md',S/'CHANGELOG.md',S/'batch_inventory.json']+[p for p in (S/'tools').glob('*.py')]+[p for p in (S/'reports').glob('*') if p.is_file() and p.name in ['collection_overview.jpg','preview_index.json','collection_resources.json','visual_review.json']]:source[p.relative_to(S).as_posix()]=p
 for relative in ['package_delivery.py','install_release.ps1','project_paths.py']:
  source['workspace_tools/'+relative]=W/'tools'/relative
 for archive,entries in [(modzip,files),(sourcezip,source)]:
  if archive==sourcezip or not archive.exists():
   with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
    for entry,p in sorted(entries.items()):z.write(p,entry)
  with zipfile.ZipFile(archive) as z:
   assert set(z.namelist())==set(entries),'Existing archive belongs to another release layout'
   assert z.testzip() is None
   for entry,p in entries.items():assert hashlib.sha256(z.read(entry)).hexdigest()==sha(p),entry
  print('COLLECTION_ARCHIVE_VERIFIED',archive.name,len(entries),flush=True)
 with zipfile.ZipFile(modzip) as z:
  for entry,p in files.items():assert z.read(entry)==(GAME/entry).read_bytes()
 report={'status':'pass','date':'2026-10-15','version':'v0.1.0','layout':'eight independent game modules in one ZIP; no merged game module','modules':validation,'mod_archive_sha256':sha(modzip),'source_archive_sha256':sha(sourcezip),'archive_module_installed_bytes_equal':True,'game_launched':False,'game_acceptance':'pending_user_test'}
 (S/'reports/collection_delivery.json').write_text(json.dumps(report,indent=2));print('COLLECTION_DELIVERY_COMPLETE',flush=True)
if __name__=='__main__':
 rows=json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters'];selected=sys.argv[1:]
 if selected==['--assemble']:assemble(rows)
 else:
  rows=[r for r in rows if not selected or r['id'] in selected]
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(deliver,rows))
