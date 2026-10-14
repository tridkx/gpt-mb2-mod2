from pathlib import Path
import subprocess,json,shutil,hashlib
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1]
PY='C:/ProgramData/anaconda3/python.exe'
BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def py(script,*extra):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/script),*extra],check=True)
def blend(script,*extra):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/script),*extra],check=True)
py('register_module.py');py('prepare_textures.py');blend('create_source.py')
py('prepare_cloth.py');py('build_cloth.py','--collision-only');py('calibrate_cloth_travel.py')
blend('apply_cloth_source.py');blend('export_geometry.py');py('calibrate_lod_cloth.py');blend('apply_cloth_source.py')
py('build_package.py');py('build_cloth.py');blend('verify_source.py')
if json.loads((R/'tools/model_config.json').read_text()).get('cloth_mode')=='mapped_outer_driver':
    # Build/cache the direct source topology first; it is the mapping input,
    # not the delivered simulation mode. Never attach its blobs to reduced LODs.
    py('verify_cloth.py')
    shutil.copy2(R/'module/YueQingShuRace/AssetPackages/yqs.tpac',R/'build/mapped_baseline_direct.tpac')
    py('build_outer_driver.py')
    shutil.copy2(R/'build/mapped_candidate.tpac',R/'module/YueQingShuRace/AssetPackages/yqs.tpac')
    blend('save_release_proxy_source.py','--',str(R));blend('verify_source.py')
    py('build_ui_runtime.py');py('verify_ui_scope.py');py('verify_preview_idle.py');py('verify_inventory_pose.py')
    py('verify_release.py');py('verify_preservation.py');py('finalize_release.py')
    py('diagnose_skirt_proxy.py');py('verify_outer_layers.py')
    completed=subprocess.run([PY,'-B','-X','utf8',str(workspace_root(R)/'tools/cloth_simulator/pipeline.py'),'--project',str(R)],check=False)
    result=json.loads((R/'reports/cloth_diagnostics.json').read_text())
    expected={'within_thresholds':0,'needs_review':1,'incomplete':2}
    current_hash=hashlib.sha256((R/'module/YueQingShuRace/AssetPackages/yqs.tpac').read_bytes()).hexdigest()
    if completed.returncode!=expected.get(result['status']) or result['inputs'].get('mod/module/YueQingShuRace/AssetPackages/yqs.tpac')!=current_hash:
        raise RuntimeError('Cloth diagnostic execution error or stale report')
    for lod in range(4):blend('render_final.py','--',str(lod))
    raise SystemExit(0)
py('build_ui_runtime.py');py('verify_ui_scope.py');py('verify_preview_idle.py');py('verify_inventory_pose.py');py('verify_release.py');py('verify_preservation.py');py('verify_cloth.py');py('verify_arm_revision.py');py('verify_feedback_fixes.py');py('verify_settled_skirt.py');py('verify_panel_motion.py');py('verify_skirt_comparison.py');py('finalize_release.py')
for lod in range(4):blend('render_final.py','--',str(lod))
