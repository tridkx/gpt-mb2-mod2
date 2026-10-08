"""Restore immutable v1.3.1 inputs from local Git if the build cache is absent."""
from pathlib import Path
import subprocess,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'tools/sleeve_config.json').read_text())
folder=ROOT/'build/sleeve_baseline';folder.mkdir(parents=True,exist_ok=True)
for old_path,name in [('module/TianxiangT5/AssetPackages/tx5.tpac','tx5.tpac'),('source/TianxiangT5_Rigged.blend','TianxiangT5_Rigged.blend'),('source/TianxiangT5_Rigged.fbx','TianxiangT5_Rigged.fbx')]:
    target=folder/name
    if not target.exists():
        result=subprocess.run(['git','show','v1.3.1:'+old_path],cwd=ROOT,check=True,capture_output=True)
        target.write_bytes(result.stdout)
assert hashlib.sha256((folder/'tx5.tpac').read_bytes()).hexdigest()==config['baseline_sha256']
print('Immutable v1.3.1 sleeve baseline ready')
