"""Rebuild this isolated race; installation is a separate workspace command."""
import subprocess,shutil,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for folder in ['build','reports','source','dist','module/TianxiangGirlT2Race/ModuleData','module/TianxiangGirlT2Race/AssetPackages']:(R/folder).mkdir(parents=True,exist_ok=True)
PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def py(name):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/name)],check=True)
def blend(name):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/name)],check=True)
blend('measure_anatomy.py');py('configure_model.py');py('prepare_references.py');py('register_module.py');blend('create_source.py');blend('prepare_cloth.py');blend('export_geometry.py');py('build_package.py')
cfg=json.loads((R/'tools/model_config.json').read_text())
if cfg['cloth_enabled']:py('build_cloth.py')
out=R/'module/TianxiangGirlT2Race/bin/Win64_Shipping_Client';out.mkdir(parents=True,exist_ok=True)
dll=out/'TianxiangGirlT2Race.UIRuntime.dll';scope=R/'reports/ui_scope_validation.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
saved=json.loads(scope.read_text()) if scope.exists() else {}
preserve=(dll.exists() and sha(dll)==saved.get('assembly_sha256') and
          hashlib.sha256((R/'tools/UIRuntime/Runtime.cs').read_text().encode()).hexdigest()==saved.get('source_sha256'))
if not preserve:
    subprocess.run(['dotnet','build',str(R/'tools/UIRuntime/UIRuntime.csproj'),'--ignore-failed-sources','-o',str(R/'build/ui_runtime')],check=True)
    shutil.copy2(R/'build/ui_runtime/TianxiangGirlT2Race.UIRuntime.dll',out)
else:print('PRESERVED_CHECKED_UI_DLL',sha(dll))
py('verify_ui_scope.py');blend('verify_source.py');py('verify_release.py');py('verify_cloth.py' if cfg['cloth_enabled'] else 'verify_skeletal_skirt.py');blend('render_final.py')
for lod in range(1,4):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools/render_final.py'),'--',str(lod)],check=True)
py('verify_preview_idle.py');py('verify_binding.py');py('verify_cloth_fit_revision.py')
if cfg['cloth_enabled']:
    py('verify_body_collision.py');py('simulate_static_cloth.py');py('verify_waist_fit.py')
    subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools/render_final.py'),'--','proxy'],check=True)
py('finalize_release.py')
