"""Sequential rebuild; stop immediately on any failed stage."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
BLENDER='D:/Blender Foundation/Blender 5.2/blender.exe'
PY='C:/ProgramData/anaconda3/python.exe'
def run(args):subprocess.run(args,check=True)
if '--preserve-input' not in sys.argv:run([PY,'-B','-X','utf8',str(R/'tools/prepare.py')])
for script in ['rig_model.py','export_geometry.py']:run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/script)])
run([PY,'-B','-X','utf8',str(R/'tools/build_package.py')])
run(['dotnet','build',str(R/'tools/Runtime/WuduRaceTest.csproj'),'--ignore-failed-sources','-o',str(R/'module/WuduRaceTest/bin/Win64_Shipping_Client')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_release.py')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_cloth.py')])
run([PY,'-B','-X','utf8',str(R/'tools/verify_hands.py')])
for script in ['add_hand_shape_keys.py','verify_source.py','render_review.py','render_hands.py','render_wrist_review.py']:run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python',str(R/'tools'/script)])
