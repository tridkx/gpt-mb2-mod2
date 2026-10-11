"""Compile and copy only the Ada UI runtime assembly."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'build/ui_runtime_dll'
subprocess.run(['dotnet', 'build', str(ROOT / 'tools/UIProbe/UIProbe.csproj'),
                '--ignore-failed-sources', '-p:AssemblyName=REAdaWongRace.UIRuntime',
                '-o', str(OUTPUT)], check=True)
target = ROOT / 'module/REAdaWongRace/bin/Win64_Shipping_Client/REAdaWongRace.UIRuntime.dll'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(OUTPUT / target.name, target)
assert target.read_bytes() == (OUTPUT / target.name).read_bytes()
