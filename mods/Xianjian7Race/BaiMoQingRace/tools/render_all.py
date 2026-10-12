"""Render all released LODs and selected actual Native motion frames."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1];BL='D:/Blender Foundation/Blender 5.2/blender.exe'
for lod in range(4):
 with (R/'build'/f'render_lod{lod}.log').open('w',encoding='utf8') as log:
  result=subprocess.run([BL,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools/render_final.py'),'--',str(lod)],stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:print((R/'build'/f'render_lod{lod}.log').read_text(encoding='utf8')[-3000:]);raise SystemExit(result.returncode)
 print('FINAL_LOD_RENDERED',R.name,lod,flush=True)
