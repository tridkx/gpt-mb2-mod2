"""Refresh final-package metadata evidence after native role alignment."""
import json,subprocess,sys,concurrent.futures
from context import SERIES,config,workspace_root
def check(path):
    root=path.parent.parent;c=config(root);w=workspace_root(root);p=root/'module'/c['id']/'AssetPackages'/(c['prefix']+'.tpac')
    audit=json.loads(subprocess.run([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(p),'--cloth-vertex-alpha'],capture_output=True,text=True,check=True).stdout);assert audit['status']=='pass'
    (root/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
    result=subprocess.run(['dotnet',str(w/'tools/AssetTool/AssetTool.dll'),'visibility',str(p)],capture_output=True,text=True,check=True)
    (root/'reports/final_visibility.json').write_text(json.dumps(json.loads(result.stdout),indent=2))
    print('FINAL_RUNTIME_AUDIT',root.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(check,SERIES.glob('*/reports/runtime_resource_fix.json')))
