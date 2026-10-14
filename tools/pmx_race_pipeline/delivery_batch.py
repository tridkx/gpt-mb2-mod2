"""Finalize, diagnose and install only the selected batch modules."""
from pathlib import Path
import json,sys,subprocess,concurrent.futures,hashlib,zipfile
from context import SERIES,config,workspace_root
from finalize import finalize

def deliver(row):
    root=Path(row['root']);c=config(root);w=workspace_root(root);log=root/'build/delivery.log';print('DELIVERY_BEGIN',c['id'],flush=True)
    try:
        finalize(root)
        with log.open('w',encoding='utf8') as out:
            result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(w/'tools/install_release.ps1'),'-Mod',c['id'],'-Version',c['version']],stdout=out,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(log.read_text(encoding='utf8',errors='replace')[-2000:])
        module=root/'module'/c['id'];installed=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules')/c['id'];archive=root/'dist'/(c['id']+'_Mod.zip');source=root/'dist'/(c['id']+'_Source.zip');z=zipfile.ZipFile(archive);files=[p for p in module.rglob('*') if p.is_file()]
        assert all(p.read_bytes()==(installed/p.relative_to(module)).read_bytes()==z.read(c['id']+'/'+p.relative_to(module).as_posix()) for p in files)
        report={'status':'pass','version':c['version'],'date':'2026-10-14','installed_module':str(installed),'installed_files':len(files),'final_package_sha256':hashlib.sha256((module/'AssetPackages'/(c['prefix']+'.tpac')).read_bytes()).hexdigest(),'mod_zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'source_zip_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'game_launched':False};(root/'reports/delivery_validation.json').write_text(json.dumps(report,indent=2));print('DELIVERY_DONE',c['id'],flush=True);return {'id':c['id'],'status':'pass','installed':str(installed)}
    except Exception as error:
        print('DELIVERY_ERROR',c['id'],str(error)[-500:],flush=True);return {'id':c['id'],'status':'error','error':str(error)}

if __name__=='__main__':
    batch=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'));requested=sys.argv[1:];rows=[r for r in batch['characters'] if not requested or r['id'] in requested];results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(deliver,rows):results.append(result)
    path=SERIES/'batch_delivery.json';previous=json.loads(path.read_text()) if path.exists() else [];combined={r['id']:r for r in previous};combined.update({r['id']:r for r in results});path.write_text(json.dumps(list(combined.values()),indent=2));assert all(r['status']=='pass' for r in results)
