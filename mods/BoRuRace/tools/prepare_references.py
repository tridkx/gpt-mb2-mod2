"""Extract current installed Native skeleton and representative animation tracks."""
from pathlib import Path
import subprocess
import re
R=Path(__file__).resolve().parents[1]
N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
skel=N/'EmAssetPackages/human/human.tpac'
subprocess.run([MB,'skeljson',str(skel),'human_skeleton',str(R/'reports/human_skeleton.json')],check=True)
for label,name in dict(idle='anim_inventory_idle',run='anim_run_forward_unarmed',bow='anim_bow',riding='anim_rider_gallop_bow',slash='anim_dagger_slashleft_1h_balance').items():
    subprocess.run([MB,'anim',str(N/'AssetPackages/animations.tpac'),name,str(R/'reports'/(label+'.json')),str(skel)],check=True)
for label,clip in [('creation_male','anim_male_custom'),('creation_female','anim_female_custom')]:
    evidence=subprocess.check_output([MB,'clip',str(N/'AssetPackages/animation_clips.tpac'),clip],text=True,encoding='utf8')
    guid=re.search(r'\banimation=([0-9a-f-]{36})',evidence).group(1)
    (R/'reports'/(label+'_clip.txt')).write_text(evidence,encoding='utf8')
    subprocess.run([MB,'anim',str(N/'AssetPackages/animations.tpac'),guid,str(R/'reports'/(label+'.json')),str(skel)],check=True)
