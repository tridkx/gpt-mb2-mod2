"""Verify final workspace/archive/install bytes and source archive completeness."""
from pathlib import Path
import json,hashlib,zipfile,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'mod.json').read_text(encoding='utf8'));ident=cfg['id'];WS=workspace_root(R);M=R/'module'/ident;I=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules')/ident
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
with zipfile.ZipFile(R/'dist'/(ident+'_Mod.zip')) as archive:
 assert archive.testzip() is None
 for p in sorted(M.rglob('*')):
  if not p.is_file() or p.name=='.gitkeep':continue
  relative=p.relative_to(M);installed=I/relative;entry=ident+'/'+relative.as_posix()
  assert p.read_bytes()==archive.read(entry)==installed.read_bytes(),relative
  rows.append(dict(path=relative.as_posix(),sha256=sha(p)))
with zipfile.ZipFile(R/'dist'/(ident+'_Source.zip')) as archive:
 assert archive.testzip() is None
 for rel in cfg['source_files']:assert archive.read(rel)==(R/rel).read_bytes(),rel
 for p in (R/'tex').rglob('*'):
  if p.is_file() and p.name!='.gitkeep':assert archive.read(p.relative_to(R).as_posix())==p.read_bytes()
 for rel in cfg['shared_source_files']:
  entry='workspace_tools/'+Path(rel).relative_to('tools').as_posix();assert archive.read(entry)==(WS/rel).read_bytes()
report=dict(status='pass',module=ident,version=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'))['version'],installed_path=str(I),files=rows,mod_archive_sha256=sha(R/'dist'/(ident+'_Mod.zip')),source_archive_sha256=sha(R/'dist'/(ident+'_Source.zip')),source_manifest_files=len(cfg['source_files']),game_launched=False,game_verified=False)
(R/'reports/delivery_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('DELIVERY_AND_INSTALL_VERIFIED',ident,len(rows))
