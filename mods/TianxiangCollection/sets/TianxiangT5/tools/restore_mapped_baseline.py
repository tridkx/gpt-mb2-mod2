"""Restore immutable v1.4.1 inputs for repeatable mapped builds."""
from pathlib import Path
import hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/mapped_baseline';OUT.mkdir(exist_ok=True)
for relative,name in [('module/TianxiangT5/AssetPackages/tx5.tpac','tx5.tpac'),('source/TianxiangT5_Rigged.blend','TianxiangT5_Rigged.blend')]:
    data=subprocess.run(['git','show','TianxiangT5/v1.4.1:mods/TianxiangT5/'+relative],cwd=ROOT,check=True,capture_output=True).stdout
    if name=='tx5.tpac':assert hashlib.sha256(data).hexdigest()=='f3eadd3fcefa0daa7789f4ec4aa81c0939c6e6e4a2882f53258e514a43f017fb'
    (OUT/name).write_bytes(data)
print('Restored immutable v1.4.1 mapped-build inputs')
