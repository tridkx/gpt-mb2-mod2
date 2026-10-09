import sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parents[1]
COMMON=next((p/'tools/cloth_compiler' for p in ROOT.parents if (p/'tools/cloth_compiler').is_dir()),BASE/'workspace_tools/cloth_compiler')
cfg=json.loads((ROOT/'tools/model_config.json').read_text(encoding="utf-8"));prefix=cfg['prefix']
inputs=ROOT/'build/cloth_cook_inputs';inputs.mkdir(exist_ok=True)
for p in inputs.glob('*.mesh.json'):p.unlink()
names=[prefix+'_'+p for p in ['head','body','legs']]
subprocess.run(['dotnet',str(BASE/'build/cloth_probe/NativeClothProbe.dll'),sys.argv[1],*names,'--dump-segments',str(inputs)],check=True,stdout=subprocess.DEVNULL)
subprocess.run([sys.executable,"-X","utf8",str(COMMON/'cook_cloth.py'),str(inputs),str(ROOT/'build/cooked_cloth'),'--policy',str(ROOT/'tools/cloth_policy.json')],check=True)
subprocess.run(['dotnet',str(BASE/'build/cloth_patch/ClothPatch.dll'),sys.argv[1],str(ROOT/'build/cooked_cloth/manifest.json'),sys.argv[2],'--allow-metameshes',*names],check=True)
