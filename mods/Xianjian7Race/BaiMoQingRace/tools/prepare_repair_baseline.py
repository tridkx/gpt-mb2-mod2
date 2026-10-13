"""Recover the accepted baseline from retained v0.1.0 delivery, if not cached."""
from pathlib import Path
import json,zipfile,hashlib,subprocess
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text());ident=cfg['id'];prefix=cfg['prefix'];B=R/'build';pkg=B/'baseline_v0.1.0.tpac'
if not pkg.exists():
 archive=R/'dist'/(ident+'_v0.1.0_Mod.zip')
 assert archive.exists(),'Keep the accepted v0.1.0 Mod ZIP in dist to reproduce baseline verification'
 with zipfile.ZipFile(archive) as z:pkg.write_bytes(z.read(ident+'/AssetPackages/'+prefix+'.tpac'))
assert hashlib.sha256(pkg.read_bytes()).hexdigest()==cfg['baseline_package_sha256']
for lod in range(4):
 folder=B/'baseline_v0.1.0_exports'/f'lod{lod}'
 if not (folder/'pack.json').exists():subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(pkg),str(folder),str(lod)]+(['--all-mips'] if lod==0 else []),check=True,stdout=subprocess.DEVNULL)
print('ACCEPTED_BASELINE_READY',ident)
