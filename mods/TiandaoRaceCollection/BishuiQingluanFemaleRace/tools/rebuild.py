"""Rebuild this isolated character, fail immediately on a failed stage."""
from pathlib import Path
import subprocess,sys,json
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe'
def py(name):subprocess.run([PY,'-B','-X','utf8',str(R/'tools'/name)],check=True)
def blend(path,*extra):subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(path),*extra],check=True)
py('prepare_references.py');py('register_module.py');blend(R/'tools/create_source.py');blend(R/'tools/export_geometry.py');py('build_package.py');py('build_cloth.py');py('build_mapped_cloth.py');py('build_ui_runtime.py');py('verify_release.py')
blend(R/'tools/save_source.py');blend(R/'tools/verify_source.py');py('configure_diagnostics.py');py('configure_sources.py')
result=subprocess.run([PY,'-B','-X','utf8',str(W/'tools/cloth_simulator/pipeline.py'),'--project',str(R)])
report=json.loads((R/'reports/cloth_diagnostics.json').read_text());assert result.returncode=={'within_thresholds':0,'needs_review':1,'incomplete':2}.get(report['status']),report['status']
for lod in range(4):blend(R/'tools/render_final.py','--',str(lod))
blend(R/'tools/render_mapped_review.py')
print('OFFLINE_BUILD_COMPLETE; game acceptance remains pending')
