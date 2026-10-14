"""Copy verified Native references with provenance; keep per-character inputs."""
from pathlib import Path
import json,shutil,hashlib,xml.etree.ElementTree as ET
from context import SERIES,config
N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
def prepare_references(root):
    version=ET.parse(N/'SubModule.xml').getroot().find('Version').get('value');assert version=='v1.4.8'
    manifest=root/'reports/native_references.json'
    if manifest.exists():
        previous=json.loads(manifest.read_text())
        if previous['game_version']==version and all((root/'reports'/name).is_file() and hashlib.sha256((root/'reports'/name).read_bytes()).hexdigest()==sha for name,sha in previous['files_sha256'].items()):return
    ref=SERIES/'EmilieRace/reports';files=['human_skeleton.json','idle.json','run.json','bow.json','riding.json','slash.json','facegen.json','facegen_clip.txt','stand_unarmed.json','stand_unarmed_clip.txt','stand_1h.json','stand_1h_clip.txt','stand_2h.json','stand_2h_clip.txt'];hashes={}
    for name in files:
        source=ref/name;dest=root/'reports'/name;shutil.copy2(source,dest);hashes[name]=hashlib.sha256(dest.read_bytes()).hexdigest()
    (root/'reports/native_references.json').write_text(json.dumps({'game_version':version,'provenance':'Verified Native v1.4.8 skeleton/animations previously extracted for Emilie; independent copies retained','files_sha256':hashes},indent=2))
if __name__=='__main__':
    batch=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'))
    for row in batch['characters']:prepare_references(Path(row['root']))
