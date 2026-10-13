"""Reproduce the stable non-simulated variant from preserved accepted geometry."""
from pathlib import Path
import json,subprocess,sys,numpy as np
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text());PY='C:/ProgramData/anaconda3/python.exe';BL='D:/Blender Foundation/Blender 5.2/blender.exe';B=R/'build'
def run(args):subprocess.run([str(a) for a in args],check=True)
def py(name):run([PY,'-X','utf8',R/'tools'/name])
def blend(name):run([BL,'--background','--factory-startup','--python-exit-code','1','--python',R/'tools'/name])
assert not cfg['cloth_enabled'];B.mkdir(exist_ok=True);py('prepare_repair_baseline.py')
if not (B/'fitted_model.npz').exists():
 py('prepare_references.py');py('prepare_textures.py');blend('create_source.py');py('prepare_cloth.py')
a=np.load(B/'cloth_alphas.npz');np.savez_compressed(B/'cloth_alphas.npz',**{n:np.zeros_like(a[n]) for n in a.files});blend('apply_cloth_source.py');blend('verify_source.py');py('register_module.py')
run(['dotnet','build',R/'tools/DisableCloth/DisableCloth.csproj','--ignore-failed-sources','-o',B/'disable_cloth']);run(['dotnet',B/'disable_cloth/DisableCloth.dll',B/'baseline_v0.1.0.tpac',R/'module'/cfg['id']/'AssetPackages'/(cfg['prefix']+'.tpac'),cfg['prefix']])
(R/'module'/cfg['id']/'ModuleData/cloth_bodies.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<bodies />\n')
py('verify_release.py');py('verify_static_cloth.py');py('verify_preview_idle.py');py('verify_ui_scope.py');py('render_all.py');py('review_previews.py')
