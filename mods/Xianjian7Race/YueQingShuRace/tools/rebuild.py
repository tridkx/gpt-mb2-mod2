from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1]
PY='C:/ProgramData/anaconda3/python.exe'
BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def py(script,*extra):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/script),*extra],check=True)
def blend(script,*extra):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/script),*extra],check=True)
py('register_module.py');py('prepare_textures.py');blend('create_source.py')
py('prepare_cloth.py');py('build_cloth.py','--collision-only');py('calibrate_cloth_travel.py')
blend('apply_cloth_source.py');blend('export_geometry.py');py('calibrate_lod_cloth.py');blend('apply_cloth_source.py')
py('build_package.py');py('build_cloth.py');blend('verify_source.py')
py('build_ui_runtime.py');py('verify_ui_scope.py');py('verify_preview_idle.py');py('verify_inventory_pose.py');py('verify_release.py');py('verify_preservation.py');py('verify_cloth.py');py('verify_arm_revision.py');py('verify_feedback_fixes.py');py('verify_settled_skirt.py');py('finalize_release.py')
for lod in range(4):blend('render_final.py','--',str(lod))
