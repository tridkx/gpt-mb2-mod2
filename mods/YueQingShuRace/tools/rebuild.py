from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1]
PY='C:/ProgramData/anaconda3/python.exe'
BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def run(args):subprocess.run(args,check=True)
for script in ['register_module.py','prepare_textures.py']:
 run([PY,'-B','-X','utf8',str(R/'tools'/script)])
for script in ['create_source.py','export_geometry.py']:
 run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/script)])
for script in ['build_package.py','verify_release.py']:
 run([PY,'-B','-X','utf8',str(R/'tools'/script)])
run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools/verify_source.py')])
for lod in range(4):
 run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools/render_final.py'),'--',str(lod)])
