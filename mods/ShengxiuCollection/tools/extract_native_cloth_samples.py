"""Regenerate read-only native cloth evidence from the installed game."""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NATIVE=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/EmAssetPackages')
PROBE=ROOT/'build/cloth_probe/NativeClothProbe.dll'
OUTPUT=ROOT/'build/cloth_segments'
for path,names in [(NATIVE/'crafting/crafting.tpac',['spear_banner_1','spear_banner_9','spear_banner_15','spear_banner_16','spear_banner_17','spear_banner_20']),
                   (NATIVE/'armor666/armor666.tpac',['clo_battania_shoulder_strap_cloak'])]:
    subprocess.run(['dotnet',str(PROBE),str(path),*names,'--dump-segments',str(OUTPUT)],
                   check=True,stdout=subprocess.DEVNULL)
print('EXTRACTED_NATIVE_CLOTH_SAMPLES_READ_ONLY')
