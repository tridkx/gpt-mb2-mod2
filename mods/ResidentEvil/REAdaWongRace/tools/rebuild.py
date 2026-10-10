"""Build only this module; delivery and installation are separate workspace commands."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLENDER = 'D:/Blender Foundation/Blender 5.2/blender.exe'
PYTHON = 'C:/ProgramData/anaconda3/python.exe'


def run(args):
    subprocess.run(args, check=True)


for script in ['register_module.py', 'prepare_model.py', 'prepare_textures.py']:
    run([PYTHON, '-B', '-X', 'utf8', str(ROOT / 'tools' / script)])
for script in ['create_source.py', 'export_geometry.py']:
    run([BLENDER, '--background', '--factory-startup', '--python-exit-code', '1', '--python', str(ROOT / 'tools' / script)])
for script in ['build_package.py', 'verify_release.py']:
    run([PYTHON, '-B', '-X', 'utf8', str(ROOT / 'tools' / script)])
run([BLENDER, '--background', '--factory-startup', '--python-exit-code', '1', '--python', str(ROOT / 'tools/verify_source.py')])
for lod in range(4):
    run([BLENDER, '--background', '--factory-startup', '--python-exit-code', '1', '--python', str(ROOT / 'tools/render_final.py'), '--', str(lod)])
if (ROOT/'build/baseline_v0.1.0/adar.tpac').exists() or (ROOT/'dist/REAdaWongRace_v0.1.0_Mod.zip').exists():
    run([PYTHON,'-B','-X','utf8',str(ROOT/'tools/verify_heels.py')])
    run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/render_heels.py')])
