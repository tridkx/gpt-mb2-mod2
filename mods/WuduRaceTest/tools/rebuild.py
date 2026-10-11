"""Sequential rebuild; stop immediately on any failed stage."""
import subprocess,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
BLENDER='D:/Blender Foundation/Blender 5.2/blender.exe'
PY='C:/ProgramData/anaconda3/python.exe'
def run(args):subprocess.run(args,check=True)
run([PY,'-B','-X','utf8',str(R/'tools/prepare.py')]+(['--preserve-input'] if '--preserve-input' in sys.argv else []))
for script in ['rig_model.py','export_geometry.py']:run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/script)])
run([PY,'-B','-X','utf8',str(R/'tools/build_package.py')])
run(['dotnet','build',str(R/'tools/Runtime/WuduRaceTest.csproj'),'--ignore-failed-sources','-o',str(R/'module/WuduRaceTest/bin/Win64_Shipping_Client')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_release.py')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_cloth.py')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_hands.py')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_inventory.py')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_fingers.py')])
scripts=['add_hand_shape_keys.py','verify_source.py','verify_face_uv.py','render_review.py','render_wrist_review.py','render_fingers.py']
if json.loads((R/'tools/model_config.json').read_text()).get('hands_render_mode')!='body':scripts.insert(-1,'render_hands.py')
for script in scripts:run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/script)])
