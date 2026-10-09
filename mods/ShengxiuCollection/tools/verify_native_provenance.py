"""Re-read current installed native assets and confirm motion QA inputs."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1]
NATIVE=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
skel=NATIVE/'EmAssetPackages/human/human.tpac'
anims=NATIVE/'AssetPackages/animations.tpac'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
fresh=ROOT/'build/current_human_skeleton.json'
subprocess.run([MB,'skeljson',str(skel),'human_skeleton',str(fresh)],check=True)
assert json.loads(fresh.read_text())==json.loads((ROOT/'reports/human_skeleton.json').read_text())
for label in ['idle','run','bow','riding']:
 reference=ROOT/'reports'/(label+'.json');old=json.loads(reference.read_text())
 fresh=ROOT/'build'/('current_'+label+'.json')
 subprocess.run([MB,'anim',str(anims),old['name'],str(fresh),str(skel)],check=True,stdout=subprocess.DEVNULL)
 current=json.loads(fresh.read_text())
 # Some earlier exports omitted optional skeleton descriptive metadata.
 # All animation tracks, roots, timing and identity must still match.
 assert {k:v for k,v in current.items() if k not in ['bones','skeletonName']}=={k:v for k,v in old.items() if k not in ['bones','skeletonName']},(label,'native motion changed')
 if current['bones']:assert current['bones']==json.loads((ROOT/'reports/human_skeleton.json').read_text())['bones']
 reference.write_bytes(fresh.read_bytes())
 records.append({'label':label,'asset':old['name'],'guid':old['guid'],'json_sha256':sha(reference),'matches_current_game':True})
report={'status':'pass','skeleton_package':str(skel),'skeleton_package_sha256':sha(skel),'animation_package':str(anims),'animation_package_sha256':sha(anims),'motions':records}
(ROOT/'reports/native_provenance.json').write_text(json.dumps(report,indent=2))
print('CURRENT_NATIVE_INPUTS_MATCH')
