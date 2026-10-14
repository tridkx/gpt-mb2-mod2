"""Build and verify this module without launching the game or installing it."""
import subprocess,sys,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def py(s):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/s)],check=True)
def blend(s,*extra):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/s),*extra],check=True)
py('prepare_references.py');py('register_module.py');blend('create_source.py');blend('export_geometry.py');py('build_package.py')
# Reuse an already verified runtime when its source and assembly are unchanged.
source=R/'tools/UIRuntime/Runtime.cs';dest=R/'module/ModernGirlRace/bin/Win64_Shipping_Client';dll=dest/'ModernGirlRace.UIRuntime.dll'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope_path=R/'reports/ui_scope_validation.json'
scope=json.loads(scope_path.read_text()) if scope_path.exists() else {}
if not (dll.exists() and scope.get('source_sha256')==sha(source) and scope.get('assembly_sha256')==sha(dll)):
    subprocess.run(['dotnet','build',str(R/'tools/UIRuntime/UIRuntime.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(R/'build/ui_obj')+'/', '-o',str(R/'build/ui_runtime')],check=True)
    import shutil
    dest.mkdir(parents=True,exist_ok=True)
    shutil.copy2(R/'build/ui_runtime/ModernGirlRace.UIRuntime.dll',dll)
py('verify_ui_scope.py');blend('verify_source.py');py('verify_release.py');blend('verify_preservation.py');py('verify_arm_binding.py')
for lod in range(4):blend('render_final.py','--',str(lod))
py('finalize_release.py')
