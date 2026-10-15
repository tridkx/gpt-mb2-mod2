"""Generate, compile, verify, package and optionally install this module only."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
MOD='WutheringUndeadRace'
GAME=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
WORKSHOP=Path('D:/SteamLibrary/steamapps/workshop/content/261550')
MODULE=ROOT/'module'/MOD
DEP=ROOT.parent/'WutheringWavesRaceCollection/module/WutheringWavesRaceCollection'
VERSION=json.loads((ROOT/'mod.json').read_text(encoding='utf-8'))['version']

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 p=subprocess.run(list(map(str,args)),cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
 print(p.stdout)
 if p.returncode:raise RuntimeError(f'Command failed ({p.returncode}): {args[0]}')
 return p.stdout

def metadata():
 m=E.Element('Module')
 for k,v in [('Name','Wuthering Undead Race'),('Id',MOD),('Version',VERSION),('DefaultModule','false'),('ModuleCategory','Singleplayer'),('ModuleType','Community'),('SingleplayerModule','true'),('MultiplayerModule','false')]:E.SubElement(m,k,value=v)
 dependencies=E.SubElement(m,'DependedModules')
 for d in ['Bannerlord.Harmony','Bannerlord.ButterLib','Bannerlord.UIExtenderEx','Bannerlord.MBOptionScreen','Native','SandBoxCore','Sandbox','WutheringWavesRaceCollection']:E.SubElement(dependencies,'DependedModule',Id=d)
 sm=E.SubElement(E.SubElement(m,'SubModules'),'SubModule')
 for k,v in [('Name','Wuthering Undead Race Runtime'),('DLLName',MOD+'.dll'),('SubModuleClassType','WutheringUndeadRace.SubModule')]:E.SubElement(sm,k,value=v)
 tags=E.SubElement(sm,'Tags')
 for k,v in [('DedicatedServerType','none'),('IsNoRenderModeElement','false')]:E.SubElement(tags,'Tag',key=k,value=v)
 xmls=E.SubElement(m,'Xmls')
 for kind,file in [('Items','items'),('Monsters','monsters'),('NPCCharacters','troops')]:
  node=E.SubElement(xmls,'XmlNode');E.SubElement(node,'XmlName',id=kind,path=file)
  types=E.SubElement(node,'IncludedGameTypes')
  for g in ['Campaign','CampaignStoryMode']:E.SubElement(types,'GameType',value=g)
 E.indent(m,space='  ');E.ElementTree(m).write(MODULE/'SubModule.xml',encoding='utf-8',xml_declaration=True)

def validate_data():
 project=E.parse(MODULE/'ModuleData/project.mbproj').getroot()
 expected={'skin':'ModuleData/skins.xml','action_set':'ModuleData/action_sets.xml','monster':'ModuleData/monsters.xml'}
 assert {f.get('type'):f.get('name') for f in project.findall('file')}==expected,'Incomplete engine resource registration'
 for f in project.findall('file'):assert (MODULE/f.get('name')).is_file(),f.attrib
 npcs=E.parse(MODULE/'ModuleData/troops.xml').getroot();items=E.parse(MODULE/'ModuleData/items.xml').getroot()
 ids=[x.get('id') for x in npcs];itemids=[x.get('id') for x in items]
 assert len(ids)==48 and len(ids)==len(set(ids)) and len(itemids)==len(set(itemids))
 gameitems={x.get('id') for f in (GAME/'Modules/SandBoxCore/ModuleData/items').glob('*.xml') for x in E.parse(f).getroot()}
 for n in npcs:
  for e in n.findall('Equipments/EquipmentRoster/equipment'):assert e.get('id').removeprefix('Item.') in gameitems|set(itemids),e.attrib
  for e in n.findall('upgrade_targets/upgrade_target'):assert e.get('id').removeprefix('NPCCharacter.') in ids
 # Every lord race shares source geometry and skeleton, changing only identity/scale.
 originals={r.get('id'):r for r in E.parse(DEP/'ModuleData/skins.xml').getroot()}
 lords=E.parse(MODULE/'ModuleData/skins.xml').getroot()
 for race in lords:
  src=originals[race.get('id').replace('wur_lord_','ww_',1)]
  for s,b in zip(race,src):
   assert float(s.get('min_scale'))==float(b.get('min_scale','1'))*1.5
   assert s.get('skeleton')==b.get('skeleton') and s.get('body_meta_mesh')==b.get('body_meta_mesh')
 sourceactions=E.parse(DEP/'ModuleData/action_sets.xml').getroot()
 actions=E.parse(MODULE/'ModuleData/action_sets.xml').getroot()
 actionids=[x.get('id') for x in actions];assert len(actionids)==len(set(actionids))
 allactions=set(actionids)|{a.get('id') for a in sourceactions}
 for a in actions:
  if a.get('base_set','').startswith('as_ww_'):assert a.get('base_set') in allactions
 for monster in E.parse(MODULE/'ModuleData/monsters.xml').getroot():
  for k in ['action_set','female_action_set']:
   if monster.get(k):assert monster.get(k) in allactions,(monster.get('id'),k,monster.get(k))
 return dict(troops=40,lords=8,custom_items=len(items),lord_races=len(lords),lord_action_sets=len(actions),engine_resource_manifest='verified')

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--install',action='store_true');args=parser.parse_args()
 if E.parse(GAME/'Modules/Native/SubModule.xml').getroot().find('Version').get('value')!='v1.4.8':raise RuntimeError('Revalidate against this game version before building')
 before={str(p.relative_to(DEP)):digest(p) for p in DEP.rglob('*') if p.is_file()}
 previous=ROOT/'reports/release_validation.json'
 if previous.is_file():
  old=json.loads(previous.read_text(encoding='utf-8'))
  if old.get('version')!=VERSION:
   history=ROOT/'reports/history'/old['version'];history.mkdir(parents=True,exist_ok=True)
   for f in ['release_validation.json','offline_tests.txt','troop_configuration.json']:
    if (ROOT/'reports'/f).is_file():shutil.copy2(ROOT/'reports'/f,history/f)
 run([sys.executable,ROOT/'tools/generate_data.py']);metadata();data=validate_data()
 run(['dotnet','build',ROOT/'source/Tests/WutheringUndeadRace.Tests.csproj','-c','Release','--nologo'])
 output=run([ROOT/'source/Tests/bin/Release/net472/WutheringUndeadRace.Tests.exe',GAME,MODULE,WORKSHOP])
 (ROOT/'reports/offline_tests.txt').write_text(output,encoding='utf-8')
 binary=MODULE/'bin/Win64_Shipping_Client';binary.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'source/Runtime/bin/Release/net472/WutheringUndeadRace.dll',binary)
 assert before=={str(p.relative_to(DEP)):digest(p) for p in DEP.rglob('*') if p.is_file()},'Dependency modified'
 manifest={str(p.relative_to(MODULE)):digest(p) for p in MODULE.rglob('*') if p.is_file() and p.name!='runtime.log'}
 report=dict(version=VERSION,game='v1.4.8',data=data,offline_tests='passed',game_acceptance='pending_user_test',module_hashes=manifest,dependency_hashes=before,dependency_unchanged=True,installed=False)
 dist=ROOT/'dist';dist.mkdir(exist_ok=True)
 package=dist/f'{MOD}_{VERSION}_Mod.zip'
 if package.exists():
  history=dist/'history';history.mkdir(exist_ok=True);shutil.copy2(package,history/(package.stem+'_'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.zip'))
 with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
  for rel in manifest:z.write(MODULE/rel,f'{MOD}/{Path(rel).as_posix()}')
 if args.install:
  installed_dep=GAME/'Modules/WutheringWavesRaceCollection'
  for rel,h in before.items():
   if not (installed_dep/rel).is_file() or digest(installed_dep/rel)!=h:raise RuntimeError('Installed WW dependency differs: '+rel)
  target=(GAME/'Modules'/MOD).resolve();assert target.parent==(GAME/'Modules').resolve() and target.name==MOD
  if target.exists():
   backup=ROOT/'build/install_backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.parent.mkdir(parents=True,exist_ok=True)
   shutil.copytree(target,backup)
  target.mkdir(exist_ok=True)
  for rel in manifest:
   dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(MODULE/rel,dst)
  assert all(digest(target/rel)==h for rel,h in manifest.items())
  report['installed']=True;report['install_path']=str(target)
 report['mod_zip']=str(package);report['mod_zip_sha256']=digest(package)
 (ROOT/'reports/release_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 source=dist/f'{MOD}_{VERSION}_Source.zip'
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
  for folder in ['source','tools','docs','reports']:
   for p in (ROOT/folder).rglob('*'):
    if p.is_file() and not set(p.relative_to(ROOT).parts)&{'bin','obj','__pycache__'}:z.write(p,f'{MOD}/{p.relative_to(ROOT).as_posix()}')
  for file in ['README.md','CHANGELOG.md','mod.json','.gitignore']:z.write(ROOT/file,f'{MOD}/{file}')
 print(json.dumps(dict(package=str(package),source=str(source),installed=report['installed'],data=data),ensure_ascii=False))

if __name__=='__main__':main()
