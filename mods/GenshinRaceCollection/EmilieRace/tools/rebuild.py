"""Rebuild only this character; do not launch or install the game."""
import subprocess,sys,json,shutil
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe';B=R/'build'
def py(name):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/name)],check=True)
def blend(name,*extra):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/name),*extra],check=True)
py('prepare.py');py('prepare_references.py');py('register_module.py');blend('create_source.py');blend('export_geometry.py');py('build_package.py');py('write_collisions.py');py('build_cloth.py')
subprocess.run(['dotnet','build',str(R/'tools/UIRuntime/UIRuntime.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(B/'ui_obj')+'/', '-o',str(B/'ui_runtime')],check=True);dest=R/'module/EmilieRace/bin/Win64_Shipping_Client';dest.mkdir(parents=True,exist_ok=True);shutil.copy2(B/'ui_runtime/EmilieRace.UIRuntime.dll',dest)
blend('verify_source.py');py('verify_release.py')
for lod in range(4):blend('render_final.py','--',str(lod))
py('save_proxy_source.py');py('finalize_release.py')
result=subprocess.run([PY,'-X','utf8',str(W/'tools/cloth_simulator/pipeline.py'),'--project',str(R)])
report=json.loads((R/'reports/cloth_diagnostics.json').read_text());assert report['status']!='error',report
blend('render_final.py','--','0','--cpu-cloth')
print('BUILD_COMPLETE',report['status'],'game test pending')
