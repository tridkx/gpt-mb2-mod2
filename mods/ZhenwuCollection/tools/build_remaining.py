"""Rebuild and verify authorized remaining sets; no installation or game launch."""
from pathlib import Path
import argparse,subprocess,sys,os,json
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1]
SETS=['04_DanyunWeiyu','05_FuyuChongyun','06_XuanjiKongmeng','07_YimoCangming','08_ShenjiTaolue']
BLENDER='D:/Blender Foundation/Blender 5.2/blender.exe'
PYTHON='C:/ProgramData/anaconda3/python.exe'
def run(folder,stage,args):
 print(folder.name,stage,flush=True);log=folder/'build'/(stage+'.log')
 env=os.environ.copy();env['DOTNET_PROCESSOR_COUNT']='2'
 with log.open('w',encoding='utf8') as out:result=subprocess.run(args,stdout=out,stderr=subprocess.STDOUT,env=env)
 if result.returncode:raise RuntimeError(stage+' failed for '+folder.name+'\n'+log.read_text(encoding='utf8',errors='replace')[-4500:])
def blender(folder,stage,extra=[]):run(folder,stage,[BLENDER,'--factory-startup','--background','--threads','4','--python-exit-code','1','--python',str(folder/'tools'/(stage+'.py'))]+(['--']+extra if extra else []))
def build(folder):
 run(folder,'verify_native_provenance',[PYTHON,'-B','-X','utf8',str(folder/'tools/verify_native_provenance.py')])
 blender(folder,'rig_model');blender(folder,'export_geometry')
 run(folder,'compile_patch',['dotnet','build',str(folder/'tools/PackagePatch/PackagePatch.csproj'),'-o',str(folder/'build/package_patch'),'-p:BaseIntermediateOutputPath='+str(folder/'build/patch_obj')+'/'])
 for stage in ['build_package','verify_release','verify_details']:run(folder,stage,[PYTHON,'-B','-X','utf8',str(folder/'tools'/(stage+'.py'))])
 blender(folder,'verify_source')
 if json.loads((folder/'tools/model_config.json').read_text()).get('cooked_cloth'):
  run(folder,'compile_cloth',[PYTHON,'-B','-X','utf8',str(ROOT/'tools/compile_cloth.py'),folder.name])
  for stage in ['verify_release','verify_details']:run(folder,'cooked_'+stage,[PYTHON,'-B','-X','utf8',str(folder/'tools'/(stage+'.py'))])
 print('BUILD_PASS',folder.name,flush=True)
def render(folder):
 blender(folder,'render_review',['final','face'])
 run(folder,'make_review_sheet',[PYTHON,'-B','-X','utf8',str(folder/'tools/make_review_sheet.py')])
 print('RENDER_READY',folder.name,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['build','render']);ap.add_argument('--sets',nargs='+',choices=SETS,default=SETS);args=ap.parse_args()
 folders=[ROOT/'sets'/n for n in args.sets]
 if args.phase=='build':
  for folder in folders:build(folder)
 else:
  with ThreadPoolExecutor(max_workers=2) as pool:
   for future in as_completed([pool.submit(render,folder) for folder in folders]):future.result()
