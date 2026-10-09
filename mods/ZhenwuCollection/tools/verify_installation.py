"""Verify complete eight-set archives, installed bytes, and accepted baseline."""
from pathlib import Path
import json,hashlib,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];MODULE=ROOT/'module/ZhenwuCollection'
INSTALLED=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/ZhenwuCollection')
config=json.loads((ROOT/'mod.json').read_text());release=json.loads((ROOT/'reports/release_validation.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert release['status']=='pass' and sha(ROOT/config['package'])==release['final_package_sha256']
for pkg in release['packages']:assert sha(ROOT/pkg['file'])==pkg['sha256']
records=[]
with zipfile.ZipFile(ROOT/'dist/ZhenwuCollection_Mod.zip') as z:
 assert z.testzip() is None;expected=set()
 for p in sorted(MODULE.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(MODULE);dest=INSTALLED/rel;entry='ZhenwuCollection/'+rel.as_posix();expected.add(entry)
  assert dest.is_file() and sha(p)==sha(dest) and z.read(entry)==p.read_bytes()
  records.append({'file':rel.as_posix(),'sha256':sha(p)})
 assert set(z.namelist())==expected
 assert {p.relative_to(INSTALLED).as_posix() for p in INSTALLED.rglob('*') if p.is_file()}=={p['file'] for p in records}
with zipfile.ZipFile(ROOT/'dist/ZhenwuCollection_Source.zip') as z:
 shared={'workspace_tools/'+Path(rel).relative_to('tools').as_posix():ROOT.parents[1]/rel for rel in config.get('shared_source_files',[])}
 assert z.testzip() is None and set(z.namelist())==set(config['source_files'])|set(shared)
 for entry,path in shared.items():assert z.read(entry)==path.read_bytes(),entry
 for rel in config['source_files']:assert z.read(rel)==(ROOT/rel).read_bytes(),rel
 for setname in config['included_sets']:
  folder=ROOT/'sets'/setname
  assert len(list((folder/'source').glob('*.blend')))==1 and len(list((folder/'source').glob('*.fbx')))==1
  for p in [*list((folder/'source').glob('*.blend')),*list((folder/'source').glob('*.fbx')),*list((folder/'tex').glob('*.png'))]:assert p.relative_to(ROOT).as_posix() in z.namelist()
with zipfile.ZipFile(ROOT/'dist/ZhenwuCollection_v1.2.0_Mod.zip') as z:
 for pkg in release['packages'][:3]:assert z.read('ZhenwuCollection/AssetPackages/'+Path(pkg['file']).name)==(ROOT/pkg['file']).read_bytes()
assert len(ET.parse(MODULE/'ModuleData/items.xml').getroot())==24
assert len(list((MODULE/'AssetPackages').glob('*.tpac')))==8
version=ET.parse(MODULE/'SubModule.xml').find('Version').get('value');assert version==release['version']=='v1.3.0'
report={'status':'pass','version':version,'installed_path':str(INSTALLED),'files':records,'module_zip_sha256':sha(ROOT/'dist/ZhenwuCollection_Mod.zip'),'source_zip_sha256':sha(ROOT/'dist/ZhenwuCollection_Source.zip'),'module_archive_installed_bytes_match':True,'all_source_archive_bytes_match':True,'game_launched':False,'game_acceptance':{p['set']:p['user_acceptance'] for p in release['packages']},'previous_three_accepted_packages_unchanged':True,'eighth_variant':'PVP'}
(ROOT/'reports/installation_validation.json').write_text(json.dumps(report,indent=2));print('INSTALLATION_AND_ZIPS_VERIFIED',version,len(records),'module files',len(config['source_files']),'source files')
