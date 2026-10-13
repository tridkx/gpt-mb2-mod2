"""Build and verify this module without launching the game or installing it."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def py(s):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/s)],check=True)
def blend(s,*extra):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/s),*extra],check=True)
py('prepare_references.py');py('prepare_model.py');py('prepare_textures.py');py('register_module.py');blend('create_source.py');blend('export_geometry.py');py('build_package.py')
subprocess.run(['dotnet','build',str(R/'tools/UIRuntime/UIRuntime.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(R/'build/ui_obj')+'/', '-o',str(R/'build/ui_runtime')],check=True)
import shutil
dest=R/'module/BoRuRace/bin/Win64_Shipping_Client';dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(R/'build/ui_runtime/BoRuRace.UIRuntime.dll',dest/'BoRuRace.UIRuntime.dll')
py('verify_ui_scope.py');blend('verify_source.py');py('verify_release.py');py('verify_preservation.py')
for lod in range(4):blend('render_final.py','--',str(lod))
py('finalize_release.py')
