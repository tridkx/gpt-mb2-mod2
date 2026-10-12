"""Rebuild this isolated race; installation is a separate workspace command."""
import subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for folder in ['build','reports','source','dist','module/TianxiangGirlT1Race/ModuleData','module/TianxiangGirlT1Race/AssetPackages']:(R/folder).mkdir(parents=True,exist_ok=True)
PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def py(name):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/name)],check=True)
def blend(name):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/name)],check=True)
py('prepare_references.py');py('register_module.py');blend('create_source.py');blend('prepare_cloth.py');blend('export_geometry.py');py('build_package.py');py('build_cloth.py')
subprocess.run(['dotnet','build',str(R/'tools/UIRuntime/UIRuntime.csproj'),'--ignore-failed-sources','-o',str(R/'build/ui_runtime')],check=True)
out=R/'module/TianxiangGirlT1Race/bin/Win64_Shipping_Client';out.mkdir(parents=True,exist_ok=True)
shutil.copy2(R/'build/ui_runtime/TianxiangGirlT1Race.UIRuntime.dll',out)
py('verify_ui_scope.py');blend('verify_source.py');py('verify_release.py');py('verify_cloth.py');blend('render_final.py')
for lod in range(1,4):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools/render_final.py'),'--',str(lod)],check=True)
py('finalize_release.py')
