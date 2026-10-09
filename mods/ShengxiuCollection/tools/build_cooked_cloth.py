"""Reproducible own-mod cloth extraction, offline cooking and TPAC insertion."""
import argparse
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
args=parser.parse_args()
inputs=ROOT/'build/cloth_cook_inputs';inputs.mkdir(exist_ok=True)
for p in inputs.glob('*.mesh.json'):p.unlink() # Dedicated own-mod generated input cache.
subprocess.run(['dotnet',str(ROOT/'build/cloth_probe/NativeClothProbe.dll'),str(args.input),
                'sx_mingyu_head','sx_mingyu_body','--dump-segments',str(inputs)],
                check=True,stdout=subprocess.DEVNULL)
assert len(list(inputs.glob('*.mesh.json')))==4
subprocess.run([sys.executable,str(ROOT/'tools/cook_cloth.py'),str(inputs),str(ROOT/'build/cooked_cloth')],check=True)
subprocess.run(['dotnet',str(ROOT/'build/cloth_patch/ClothPatch.dll'),str(args.input),
                str(ROOT/'build/cooked_cloth/manifest.json'),str(args.output)],check=True)
