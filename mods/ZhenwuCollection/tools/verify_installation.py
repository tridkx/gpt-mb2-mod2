"""Check complete installed module and both delivery archives byte-for-byte."""
from pathlib import Path
import json,hashlib,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'module/ZhenwuCollection'
INSTALLED=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/ZhenwuCollection')
config=json.loads((ROOT/'mod.json').read_text());release=json.loads((ROOT/'reports/release_validation.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/config['package'])==release['final_package_sha256']
records=[]
with zipfile.ZipFile(ROOT/'dist/ZhenwuCollection_Mod.zip') as z:
 assert z.testzip() is None
 expected=set()
 for p in sorted(MODULE.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(MODULE);dest=INSTALLED/rel;entry='ZhenwuCollection/'+rel.as_posix();expected.add(entry)
  assert dest.is_file() and sha(p)==sha(dest)
  assert z.read(entry)==p.read_bytes()
  records.append({'file':rel.as_posix(),'sha256':sha(p)})
 assert set(z.namelist())==expected
 assert {p.relative_to(INSTALLED).as_posix() for p in INSTALLED.rglob('*') if p.is_file()}=={p['file'] for p in records}
with zipfile.ZipFile(ROOT/'dist/ZhenwuCollection_Source.zip') as z:
 assert z.testzip() is None and set(z.namelist())==set(config['source_files'])
 for rel in config['source_files']:assert z.read(rel)==(ROOT/rel).read_bytes(),rel
 for rel in ['sets/01_YunhaiNiezong/source/ZhenwuYunhai_Rigged.blend','sets/01_YunhaiNiezong/source/ZhenwuYunhai_Rigged.fbx','sets/01_YunhaiNiezong/tex/eyelash_D.png']:assert rel in z.namelist()
version=ET.parse(MODULE/'SubModule.xml').find('Version').get('value')
assert version==release['version']
report={'status':'pass','version':version,'installed_path':str(INSTALLED),'files':records,'module_zip_sha256':sha(ROOT/'dist/ZhenwuCollection_Mod.zip'),'source_zip_sha256':sha(ROOT/'dist/ZhenwuCollection_Source.zip'),'module_archive_installed_bytes_match':True,'all_source_archive_bytes_match':True,'game_launched':False,'game_acceptance':'pending'}
(ROOT/'reports/installation_validation.json').write_text(json.dumps(report,indent=2));print('INSTALLATION_AND_ZIPS_VERIFIED',version,len(records),'module files',len(config['source_files']),'source files')
