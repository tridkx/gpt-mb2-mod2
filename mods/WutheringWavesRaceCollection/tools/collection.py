"""Build, validate and install one module while preserving character source projects."""
from pathlib import Path
import copy,concurrent.futures,hashlib,json,shutil,subprocess,sys,tempfile,zipfile
import xml.etree.ElementTree as ET
S=Path(__file__).resolve().parents[1]
W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(W/'tools'))
from cloth_simulator.pipeline import ensure_diagnostics,delivery_files
ID='WutheringWavesRaceCollection';VERSION='v0.1.1'
GAME=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def roots():return [S/r['id'] for r in json.loads((S/'batch_inventory.json').read_text(encoding='utf8'))['characters']]
def hashes(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def canonical(n):return n.tag,sorted(n.attrib.items()),(n.text or '').strip(),[canonical(c) for c in n]
def write(p,n):
 p.parent.mkdir(parents=True,exist_ok=True);ET.indent(n);ET.ElementTree(n).write(p,encoding='utf-8',xml_declaration=True)
def diagnostic(root):
 cfg=json.loads((root/'mod.json').read_text(encoding='utf8'));r=ensure_diagnostics(root,cfg)
 return {'id':root.name,'status':r['status'],'fingerprint':r['fingerprint']}
def build():
 components=roots();(S/'build').mkdir(exist_ok=True);(S/'tex').mkdir(exist_ok=True)
 stage=Path(tempfile.mkdtemp(prefix='collection_',dir=S/'build'))
 merged={};descriptor=None;submodules=[];assets=[];component_versions={}
 for root in components:
  c=json.loads((root/'tools/model_config.json').read_text(encoding='utf8'))
  cfg=json.loads((root/'mod.json').read_text(encoding='utf8'));r=json.loads((root/cfg['validation_report']).read_text())
  assert r['status']=='pass' and r['version']==c['version'] and r['final_package_sha256']==sha(root/cfg['package'])
  src=root/'module'/root.name;d=ET.parse(src/'SubModule.xml').getroot();component_versions[root.name]=d.find('Version').get('value')
  if descriptor is None:descriptor=copy.deepcopy(d)
  submodules.extend(copy.deepcopy(list(d.find('SubModules'))))
  for p in src.rglob('*'):
   if not p.is_file() or p.name in ['.gitkeep','SubModule.xml','project.mbproj']:continue
   rel=p.relative_to(src)
   if rel.parts[0]=='ModuleData' and p.suffix=='.xml':
    node=ET.parse(p).getroot()
    if p.name not in merged:merged[p.name]=ET.Element(node.tag,node.attrib)
    assert merged[p.name].tag==node.tag;merged[p.name].extend(copy.deepcopy(list(node)))
   else:
    dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert dest.read_bytes()==p.read_bytes(),rel
    else:shutil.copy2(p,dest)
    assets.append({'component':root.name,'file':rel.as_posix(),'sha256':sha(p)})
 for filename,node in merged.items():
  ids=[n.get('id') or n.get('name') for n in node];ids=[x for x in ids if x is not None]
  assert len(ids)==len(set(ids)),filename;write(stage/'ModuleData'/filename,node)
  for root in components:
   original=root/'module'/root.name/'ModuleData'/filename
   if not original.exists():continue
   for child in ET.parse(original).getroot():
    identity=child.get('id') or child.get('name');matches=[n for n in node if (n.get('id') or n.get('name'))==identity]
    assert len(matches)==1 and canonical(child)==canonical(matches[0]),(root.name,filename,identity)
 assert len(merged['skins.xml'])==len(merged['test_troop.xml'])==len(submodules)==8
 for tag,value in [('Id',ID),('Name','Wuthering Waves Race Collection'),('Version',VERSION)]:descriptor.find(tag).set('value',value)
 descriptor.find('SubModules').clear();descriptor.find('SubModules').extend(submodules);write(stage/'SubModule.xml',descriptor)
 shutil.copy2(components[0]/'module'/components[0].name/'ModuleData/project.mbproj',stage/'ModuleData/project.mbproj')
 module=S/'module'/ID;module.parent.mkdir(exist_ok=True)
 if module.exists():
  assert module.resolve().parent==(S/'module').resolve();previous=Path(tempfile.mkdtemp(prefix='previous_module_',dir=S/'build'))/ID;module.rename(previous)
 stage.rename(module)
 subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','guidindex',str(module/'AssetPackages'),str(S/'reports/collection_asset_index.tsv')],check=True)
 index=[line.split('\t') for line in (S/'reports/collection_asset_index.tsv').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
 assert len({r[0] for r in index})==len(index) and len({r[2] for r in index})==len(index)
 sys.path.insert(0,str(W/'tools'));from race_action_sets import validate
 native_actions=ET.parse(GAME/'Native/ModuleData/action_sets.xml').getroot()
 for root in components:
  c=json.loads((root/'tools/model_config.json').read_text(encoding='utf8'))
  own_actions=ET.Element('action_sets');own_actions.extend(n for n in merged['action_sets.xml'] if n.get('skeleton')==c['skeleton'])
  v=validate(native_actions,own_actions,c['race'],c['skeleton']);assert v['status']=='pass',v
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:diagnostics=list(pool.map(diagnostic,components))
 (S/'reports/collection_cloth_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
 report={'status':'pass','version':VERSION,'date':'2026-10-15','components':[r.name for r in components],'component_versions':component_versions,'race_count':8,'submodule_count':8,'unique_asset_count':len(index),'unchanged_component_assets':assets,'module_file_hashes':hashes(module),'xml_counts':{k:len(v) for k,v in merged.items()},'final_package_sha256':sha(module/'AssetPackages/ww_jinhsi.tpac'),'game_verified':False}
 (S/'reports/collection_validation.json').write_text(json.dumps(report,indent=2))
 sources=['README.md','CHANGELOG.md','mod.json','batch_inventory.json']
 for p in module.rglob('*'):
  if p.is_file():sources.append(p.relative_to(S).as_posix())
 for p in (S/'tools').glob('*.py'):sources.append(p.relative_to(S).as_posix())
 for p in (S/'reports').rglob('*'):
  if p.is_file() and p.suffix in ['.json','.jpg','.png','.tsv'] and p.name not in ['collection_delivery.json','collection_installation.json']:sources.append(p.relative_to(S).as_posix())
 for root in components:
  for p in root.rglob('*'):
   if p.is_file() and not any(x in p.relative_to(root).parts for x in ['build','dist','obj','bin','__pycache__']) and p.suffix not in ['.log','.blend1','.blend2','.pyc']:sources.append(p.relative_to(S).as_posix())
  local,_=delivery_files(root,json.loads((root/'reports/cloth_diagnostics.json').read_text()))
  for p,entry in local:
   if p.is_relative_to(root/'build'):
    dest=S/'reports/cloth_diagnostics'/root.name/entry;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);sources.append(dest.relative_to(S).as_posix())
 shared=[]
 for base in ['pmx_race_pipeline','asset_helpers','cloth_compiler','cloth_simulator']:
  shared += [p.relative_to(W).as_posix() for p in (W/'tools'/base).rglob('*') if p.is_file() and p.suffix in ['.py','.tpl','.cs','.csproj','.md','.html'] and not any(x in p.parts for x in ['obj','bin','__pycache__'])]
 shared+=['tools/race_action_sets.py','tools/package_delivery.py','tools/install_release.ps1','tools/project_paths.py']
 cfg={'id':ID,'package':f'module/{ID}/AssetPackages/ww_jinhsi.tpac','validation_report':'reports/collection_validation.json','source_files':sorted(set(sources)),'shared_source_files':sorted(set(shared)),'collection_components':[r.name for r in components]}
 (S/'mod.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8');print('COLLECTION_BUILT',flush=True)
def install():
 module=S/'module'/ID;report=json.loads((S/'reports/collection_validation.json').read_text());assert hashes(module)==report['module_file_hashes']
 assert not any('Bannerlord' in p or 'TaleWorlds' in p for p in subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace').splitlines()),'Exit game and launcher before installation'
 subprocess.run([shutil.which('pwsh'),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/install_release.ps1'),'-Mod',ID,'-Version',VERSION],check=True)
 archive=S/'dist'/(ID+'_Mod.zip')
 with zipfile.ZipFile(archive) as z:
  for p in module.rglob('*'):
   if p.is_file():assert p.read_bytes()==(GAME/ID/p.relative_to(module)).read_bytes()==z.read(ID+'/'+p.relative_to(module).as_posix())
 backup=S/'build/installed_independent_modules_v0.1.0';backup.mkdir(exist_ok=True);moved=[]
 for root in roots():
  target=(GAME/root.name).resolve();dest=(backup/root.name).resolve()
  assert target.parent==GAME.resolve() and dest.parent==backup.resolve() and root.name not in ['Native','Sandbox','SandBoxCore']
  if not target.exists():continue
  assert not dest.exists();before=hashes(target);target.rename(dest);assert hashes(dest)==before;moved.append(root.name)
 for kind in ['Mod','Source']:
  src=S/'dist'/(ID+'_'+kind+'.zip');dest=S/'dist'/(ID+'_'+VERSION+'_'+kind+'.zip');assert not dest.exists();shutil.copy2(src,dest);assert sha(src)==sha(dest)
 report={'status':'pass','version':VERSION,'date':'2026-10-15','installed_module':str(GAME/ID),'module_count':1,'backed_up_independent_modules':moved,'backup':str(backup),'module_file_hashes':hashes(module),'mod_archive_sha256':sha(archive),'source_archive_sha256':sha(S/'dist'/(ID+'_Source.zip')),'game_launched':False,'game_verified':False}
 (S/'reports/collection_installation.json').write_text(json.dumps(report,indent=2));(S/'reports/collection_delivery.json').write_text(json.dumps(report,indent=2));print('COLLECTION_INSTALLED',flush=True)
if __name__=='__main__':
 if sys.argv[1]=='build':build()
 elif sys.argv[1]=='install':install()
 else:raise ValueError('Use build or install')
