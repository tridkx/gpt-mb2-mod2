"""Rebuild one isolated fixed Pal7 race; fail before delivery on any check."""
from pathlib import Path
import subprocess,sys,json,shutil,argparse
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe'
parser=argparse.ArgumentParser();parser.add_argument('--start',type=int,default=0);parser.add_argument('--stop',type=int,default=99);parser.add_argument('--reuse-textures',action='store_true');args=parser.parse_args()
def py(name,*extra):return [PY,'-B','-X','utf8',str(R/'tools'/name),*extra]
def blend(name,*extra):return [BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/name),*extra]
steps=[py('prepare_textures.py'),blend('create_source.py'),py('register_module.py'),py('prepare_cloth.py'),py('build_cloth.py','--collision-only'),py('calibrate_cloth_travel.py'),blend('apply_cloth_source.py'),blend('export_geometry.py'),py('calibrate_lod_cloth.py'),blend('apply_cloth_source.py'),py('build_package.py',*(['--reuse-textures'] if '--reuse-textures' in sys.argv else [])),py('build_cloth.py'),['dotnet','build',str(R/'tools/UIRuntime/UIRuntime.csproj'),'--ignore-failed-sources','-o',str(R/'build/ui_runtime')],py('verify_ui_scope.py'),blend('verify_source.py'),py('verify_release.py'),py('verify_cloth.py'),py('verify_preview_idle.py'),py('render_all.py'),py('review_previews.py')]
if args.start==0:subprocess.run(py('prepare_references.py'),check=True)
for i,command in enumerate(steps):
 if not args.start<=i<=args.stop:continue
 print('STEP',i,command,flush=True)
 with (R/'build'/f'step_{i:02d}.log').open('w',encoding='utf8') as log:
  process=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 if process.returncode:
  print((R/'build'/f'step_{i:02d}.log').read_text(encoding='utf8')[-5000:]);raise SystemExit(process.returncode)
 if i==12:
  out=R/'module'/cfg['id']/'bin/Win64_Shipping_Client';out.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'build/ui_runtime'/(cfg['id']+'.UIRuntime.dll'),out)
 print('STEP_PASS',i,flush=True)
