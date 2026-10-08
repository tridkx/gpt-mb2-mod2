"""Rebase onto the exact game-tested v1.5.0 package; change one wind field."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/wind_control';OUT.mkdir(exist_ok=True)
config=json.loads((ROOT/'tools/wind_control_config.json').read_text());tag=config['baseline_tag']
def restore(relative,out):
    data=subprocess.run(['git','show',tag+':mods/TianxiangT5/'+relative],check=True,capture_output=True).stdout
    out.parent.mkdir(exist_ok=True,parents=True);out.write_bytes(data);return data
baseline=restore('module/TianxiangT5/AssetPackages/tx5.tpac',OUT/'baseline.tpac')
assert hashlib.sha256(baseline).hexdigest()==config['baseline_package_sha256']
source_hashes={}
for name in ['TianxiangT5_Rigged.blend','TianxiangT5_Rigged.fbx','TianxiangT5_ClothSimulation.blend','TianxiangT5_ClothSimulation.fbx']:
    data=restore('source/'+name,ROOT/'source'/name);source_hashes[name]=hashlib.sha256(data).hexdigest()
(OUT/'source_hashes.json').write_text(json.dumps(source_hashes,indent=2))
subprocess.run(['dotnet',str(ROOT/'build/sleeve_tool/bin/SleeveTool.dll'),'windoff',str(OUT/'baseline.tpac'),str(OUT/'tx5.tpac')],check=True)
