"""Extract current installed Native skeleton and representative animation tracks."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1]
N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
skel=N/'EmAssetPackages/human/human.tpac'
subprocess.run([MB,'skeljson',str(skel),'human_skeleton',str(R/'reports/human_skeleton.json')],check=True)
for label,name in dict(idle='anim_inventory_idle',run='anim_run_forward_unarmed',bow='anim_bow',riding='anim_rider_gallop_bow',slash='anim_dagger_slashleft_1h_balance',
                      stand_unarmed1='anim_unarmed_stand_idle_1',stand_unarmed2='anim_unarmed_stand_idle_2',stand_unarmed3='anim_unarmed_stand_idle_3',
                      stand_onehand='anim_1h_without_shield_stand_idle_1',stand_twohand='anim_2h_stand_idle_1',
                      ui_neutral_male='anim_female_idle_long',ui_neutral_female='anim_female_idle_long').items():
    subprocess.run([MB,'anim',str(N/'AssetPackages/animations.tpac'),name,str(R/'reports'/(label+'.json')),str(skel)],check=True)
