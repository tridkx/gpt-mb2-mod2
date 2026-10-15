"""Build, verify, package and install the two independent bandit modules only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

IDS=('BanditPopulationTuning','GenshinBanditRace')
NAMES=dict(BanditPopulationTuning='Bandit Population Tuning',GenshinBanditRace='Genshin Bandit Race')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run(command):
    result=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'DOTNET_CLI_UI_LANGUAGE':'en-US'})
    print(result.stdout,end=''); print(result.stderr,end='')
    if result.returncode: raise RuntimeError(f'Command failed ({result.returncode}): {command[0]}')
    return result.stdout
def xml_write(path,root):
    path.parent.mkdir(parents=True,exist_ok=True); ET.indent(root,space='  ')
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def installed_document(text):
    text=text.replace('[Genshin Bandit Race](../GenshinBanditRace/README.md)','Genshin Bandit Race')
    text=text.replace('[Bandit Population Tuning](../BanditPopulationTuning/README.md)','Bandit Population Tuning')
    return re.sub(r'\[([^\]]+)\]\((reports/[^)]+)\)',lambda m:f'{m[1]}（见源码包 `{m[2]}`）',text)
def descriptor(module,identity):
    root=ET.Element('Module')
    for tag,value in [('Name',NAMES[identity]),('Id',identity),('Version','v1.0.0'),('DefaultModule','false'),
                      ('ModuleCategory','Singleplayer'),('Official','false'),('ModuleType','Community'),('SingleplayerModule','true'),('MultiplayerModule','false')]:
        ET.SubElement(root,tag,value=value)
    dependencies=ET.SubElement(root,'DependedModules')
    for dep in ['Bannerlord.Harmony','Bannerlord.ButterLib','Bannerlord.UIExtenderEx','Bannerlord.MBOptionScreen','Native','SandBoxCore','Sandbox']:
        ET.SubElement(dependencies,'DependedModule',Id=dep)
    if identity=='GenshinBanditRace': ET.SubElement(dependencies,'DependedModule',Id='GenshinRaceCollection')
    subs=ET.SubElement(root,'SubModules')
    entries=[(NAMES[identity]+' Runtime',identity+'.dll',identity+'.SubModule')]
    if identity=='GenshinBanditRace': entries.append(('Shared Troop Armor Runtime','RaceTroopBuilder.ArmorRuntime.dll','RaceTroopBuilder.ArmorRuntime.SubModule'))
    for name,dll,cls in entries:
        sub=ET.SubElement(subs,'SubModule')
        for tag,value in [('Name',name),('DLLName',dll),('SubModuleClassType',cls)]: ET.SubElement(sub,tag,value=value)
        tags=ET.SubElement(sub,'Tags')
        for key,value in [('DedicatedServerType','none'),('IsNoRenderModeElement','false')]: ET.SubElement(tags,'Tag',key=key,value=value)
    xmls=ET.SubElement(root,'Xmls')
    if identity=='GenshinBanditRace':
        node=ET.SubElement(xmls,'XmlNode'); ET.SubElement(node,'XmlName',id='NPCCharacters',path='troops')
        ET.SubElement(ET.SubElement(node,'IncludedGameTypes'),'GameType',value='Campaign')
    xml_write(module/'SubModule.xml',root)

def build(root,identity,args,dependencies):
    game=args.game_root.resolve(); module=root/'module'/identity
    (module/'ModuleData').mkdir(parents=True,exist_ok=True)
    descriptor(module,identity)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report_dir=root/'reports'; report_dir.mkdir(exist_ok=True)
    (root/'dist').mkdir(exist_ok=True)
    if identity=='GenshinBanditRace':
        run(['python',root/'tools/generate_data.py','--game-root',game])
        armor_root=next((p/'mods/RaceTroopBuilder' for p in root.parents if (p/'mods/RaceTroopBuilder/source/Runtime/bin/Release/net472/RaceTroopBuilder.ArmorRuntime.dll').is_file()),root/'workspace_tools/RaceTroopBuilder')
        armor_dll=armor_root/'source/Runtime/bin/Release/net472/RaceTroopBuilder.ArmorRuntime.dll'
        module_bin=module/'bin/Win64_Shipping_Client'; module_bin.mkdir(parents=True,exist_ok=True)
        if not armor_dll.is_file(): armor_dll=module_bin/'RaceTroopBuilder.ArmorRuntime.dll'
        if not armor_dll.is_file(): raise FileNotFoundError('RaceTroopBuilder armor provider is missing')
        if armor_dll.resolve()!= (module_bin/armor_dll.name).resolve(): shutil.copy2(armor_dll,module_bin/armor_dll.name)
    mcm=Path(dependencies['Bannerlord.MBOptionScreen']['root'])/'bin/Win64_Shipping_Client'
    harmony=Path(dependencies['Bannerlord.Harmony']['root'])/'bin/Win64_Shipping_Client'
    build_args=['-c','Release','--nologo',f'-p:GameRoot={game}',f'-p:McmBin={mcm}',f'-p:HarmonyBin={harmony}']
    run(['dotnet','build',root/'source/Tests'/f'{identity}.Tests.csproj',*build_args])
    tests=root/'source/Tests/bin/Release/net472'
    shutil.copy2(harmony/'0Harmony.dll',tests/'0Harmony.dll')
    if identity=='GenshinBanditRace': shutil.copy2(module/'bin/Win64_Shipping_Client/RaceTroopBuilder.ArmorRuntime.dll',tests/'RaceTroopBuilder.ArmorRuntime.dll')
    output=run([tests/f'{identity}.Tests.exe',game,module,args.workshop_root])
    (report_dir/'offline_tests.txt').write_text(output,encoding='utf-8')
    checks=int(re.search(r'PASS (\d+) checks',output).group(1))
    module_bin=module/'bin/Win64_Shipping_Client'; module_bin.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/'source/Runtime/bin/Release/net472'/f'{identity}.dll',module_bin/f'{identity}.dll')
    (module/'README.zh-CN.md').write_text(installed_document((root/'README.md').read_text(encoding='utf-8')),encoding='utf-8')
    shutil.copy2(root/'CHANGELOG.md',module/'CHANGELOG.md')
    if (root/'docs').exists(): shutil.copytree(root/'docs',module/'docs',dirs_exist_ok=True)
    if identity=='GenshinBanditRace':
        (module/'reports').mkdir(exist_ok=True)
        shutil.copy2(report_dir/'troop_configuration.json',module/'reports/troop_configuration.json')
    files={p.relative_to(module).as_posix():p for p in module.rglob('*') if p.is_file() and p.name!='runtime.log'}
    hashes={k:sha(v) for k,v in files.items()}
    info=dict(id=identity,version='v1.0.0',generated_utc=stamp,status='pass',checks=checks,prerequisites=dependencies,
        game_version=ET.parse(game/'Modules/Native/SubModule.xml').getroot().find('Version').get('value'),
        module_files_sha256=hashes,patch_targets=[x for x in output.splitlines() if x.startswith('PATCH OK')],
        game_inputs_sha256={str(p.relative_to(game)):sha(p) for p in [game/'Modules/Native/SubModule.xml',
            game/'bin/Win64_Shipping_Client/TaleWorlds.CampaignSystem.dll',game/'Modules/SandBox/bin/Win64_Shipping_Client/SandBox.dll']},
        game_acceptance='pending_user_test; game_not_started')
    if identity=='GenshinBanditRace':
        installed_dep=game/'Modules/GenshinRaceCollection'
        source_dep=next((p/'mods/GenshinRaceCollection/module/GenshinRaceCollection' for p in root.parents
                         if (p/'mods/GenshinRaceCollection/module/GenshinRaceCollection/SubModule.xml').is_file()),installed_dep)
        # Do not overwrite this dependency; verify the full installed collection matches its source.
        dep_hashes={p.relative_to(source_dep).as_posix():sha(p) for p in source_dep.rglob('*') if p.is_file()}
        assert all((installed_dep/k).is_file() and sha(installed_dep/k)==v for k,v in dep_hashes.items()),'Genshin collection source/install mismatch'
        info['race_dependency_sha256']=dep_hashes
    (report_dir/'release_validation.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    archive=root/'dist'/f'{identity}_v1.0.0_{stamp}.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for relative,path in files.items(): z.write(path,f'{identity}/{relative}')
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==len(hashes)
        assert all(hashlib.sha256(z.read(f'{identity}/{k}')).hexdigest()==v for k,v in hashes.items())
    if args.install:
        modules_root=(game/'Modules').resolve(); destination=(modules_root/identity).resolve()
        assert destination.parent==modules_root and destination.name==identity
        if destination.exists(): shutil.copytree(destination,root/'build/install_backups'/stamp/identity)
        for relative,path in files.items():
            target=destination/relative; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,target)
        actual={k:sha(destination/k) for k in hashes}
        assert actual==hashes
        installation=dict(status='pass',installed_path=str(destination),generated_utc=stamp,installed_files_sha256=actual,
                          settings='MCM per-save data; installation does not touch user settings or saves')
        (report_dir/'installation_validation.json').write_text(json.dumps(installation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'INSTALLED {destination}')
    source=root/'dist'/f'{identity}_v1.0.0_source_{stamp}.zip'
    with zipfile.ZipFile(source,'x',zipfile.ZIP_DEFLATED) as z:
        for path in root.rglob('*'):
            parts=path.relative_to(root).parts
            if not path.is_file() or parts[0] in ['build','dist'] or 'obj' in parts or '__pycache__' in parts or path.name=='runtime.log': continue
            if parts[0]=='source' and 'bin' in parts: continue
            z.write(path,f'{identity}/'+path.relative_to(root).as_posix())
        z.write(Path(__file__),f'{identity}/workspace_tools/bandit_mod_release.py')
        if identity=='GenshinBanditRace':
            for relative in ['source/Runtime/SubModule.cs','source/Runtime/RaceTroopBuilder.ArmorRuntime.csproj','source/Runtime/Harmony-LICENSE.txt','source/Shared/ArmorProtocol.cs']:
                z.write(armor_root/relative,f'{identity}/workspace_tools/RaceTroopBuilder/{relative}')
    print(f'PACKAGE {archive}\nSOURCE {source}')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod',choices=IDS,required=True)
    parser.add_argument('--project-root',type=Path)
    parser.add_argument('--game-root',type=Path,default=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord'))
    parser.add_argument('--workshop-root',type=Path)
    parser.add_argument('--install',action='store_true')
    args=parser.parse_args()
    args.workshop_root=(args.workshop_root or args.game_root.parent.parent/'workshop/content/261550').resolve()
    root=args.project_root or Path(__file__).resolve().parents[1]/'mods'/args.mod
    dependencies={}
    for base in [args.game_root/'Modules',args.workshop_root]:
        for xml in base.glob('*/SubModule.xml'):
            module=ET.parse(xml).getroot(); identity=module.find('Id').get('value')
            if identity in ['Bannerlord.Harmony','Bannerlord.ButterLib','Bannerlord.UIExtenderEx','Bannerlord.MBOptionScreen']:
                dependencies.setdefault(identity,dict(root=str(xml.parent),version=module.find('Version').get('value')))
    assert len(dependencies)==4,'MCM and its three prerequisites are required'
    protected=[args.game_root/'Modules/Native/SubModule.xml',args.game_root/'bin/Win64_Shipping_Client/TaleWorlds.CampaignSystem.dll',
               args.game_root/'Modules/SandBox/bin/Win64_Shipping_Client/SandBox.dll']
    protected += [p for d in dependencies.values() for p in Path(d['root']).rglob('*') if p.is_file()]
    before={str(p):sha(p) for p in protected}
    build(root.resolve(),args.mod,args,dependencies)
    changed=[p for p in protected if before[str(p)]!=sha(p)]
    assert not changed,'Game or workshop prerequisites changed: '+str(changed)

if __name__=='__main__': main()
