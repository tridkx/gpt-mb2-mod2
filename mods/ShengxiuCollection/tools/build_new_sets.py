"""Rebuild Baifeng/Suwen using their committed set scripts and parameters."""
import subprocess,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BLENDER='D:/Blender Foundation/Blender 5.2/blender.exe'
parser=argparse.ArgumentParser();parser.add_argument('--set',choices=['02_Baifeng','03_Suwen'],action='append')
args=parser.parse_args()
common=next((p/'tools/cloth_compiler' for p in ROOT.parents if (p/'tools/cloth_compiler').is_dir()),ROOT/'workspace_tools/cloth_compiler')
def run(args):subprocess.run([str(a) for a in args],check=True)
for project,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch')]:
 run(['dotnet','build',common/(project+'.csproj'),'-o',ROOT/'build'/folder,'--nologo','-v','quiet'])
for name in args.set or ['02_Baifeng','03_Suwen']:
 root=ROOT/'sets'/name
 for folder in ['build','source','reports','build/mesh','module/ShengxiuCollection/AssetPackages']:(root/folder).mkdir(parents=True,exist_ok=True)
 run(['dotnet','build',root/'tools/PackagePatch/PackagePatch.csproj','-o',root/'build/package_patch','--nologo','-v','quiet'])
 if name=='03_Suwen':run([sys.executable,'-X','utf8',root/'tools/prepare_eye_textures.py'])
 for script in ['rig_model.py','export_geometry.py']:
  run([BLENDER,'--background','--python-exit-code','1','--python',root/'tools'/script])
 for script in ['build_package.py','verify_release.py']:
  run([sys.executable,'-X','utf8',root/'tools'/script])
 run([sys.executable,'-X','utf8',ROOT/'tools/verify_set_cloth.py',name])
 run([BLENDER,'--background','--python-exit-code','1','--python',root/'tools/verify_source.py'])
 run([BLENDER,'--background','--python-exit-code','1','--python',root/'tools/render_review.py','--','final','face'])
run([sys.executable,'-X','utf8',ROOT/'tools/verify_head_follow.py',*(args.set or [])])
print('NEW_SET_BUILDS_CHECKED; run prepare_collection_release.py after reviewing previews')
