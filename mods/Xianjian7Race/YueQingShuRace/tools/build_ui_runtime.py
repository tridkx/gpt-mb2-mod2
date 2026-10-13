"""Build only the own-race inventory preview adapter and selected clip references."""
from pathlib import Path
import subprocess,shutil
R=Path(__file__).resolve().parents[1];B=R/'build';N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native');MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
for label in ['ui_neutral_male','ui_neutral_female']:subprocess.run([MB,'anim',str(N/'AssetPackages/animations.tpac'),'anim_female_idle_long',str(R/'reports'/(label+'.json')),str(N/'EmAssetPackages/human/human.tpac')],check=True)
subprocess.run(['dotnet','build',str(R/'tools/UIRuntime/UIRuntime.csproj'),'--ignore-failed-sources','-o',str(B/'ui_runtime')],check=True)
out=R/'module/YueQingShuRace/bin/Win64_Shipping_Client';out.mkdir(parents=True,exist_ok=True);shutil.copy2(B/'ui_runtime/YueQingShuRace.UIRuntime.dll',out)
