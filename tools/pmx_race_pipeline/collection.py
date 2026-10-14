"""Build one installable collection without changing the character packages."""
from pathlib import Path
import copy,hashlib,json,shutil,sys,zipfile,subprocess,concurrent.futures
import xml.etree.ElementTree as ET
from context import SERIES,workspace_root
from finalize import finalize

ID='GenshinRaceCollection'
VERSION='v0.1.0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def roots():
    rows=json.loads((SERIES/'batch_inventory.json').read_text(encoding='utf8'))['characters']
    return [SERIES/'EmilieRace']+[SERIES/r['id'] for r in rows]
def diagnostic(root):
    if root.name=='EmilieRace':
        result=json.loads((root/'reports/cloth_diagnostics.json').read_text(encoding='utf8'))
        assert result['package_sha256']==sha(root/'module/EmilieRace/AssetPackages/emilie.tpac') and result['status']!='error'
        return {'id':root.name,'status':result['status'],'preserved_existing_report':True}
    finalize(root)
    w=workspace_root(root);sys.path.insert(0,str(w/'tools'))
    from cloth_simulator.pipeline import ensure_diagnostics
    c=json.loads((root/'mod.json').read_text(encoding='utf8'))
    result=ensure_diagnostics(root,c) if 'cloth_diagnostics' in c else None
    return {'id':root.name,'status':result['status'] if result else 'not_configured'}
def build():
    w=workspace_root(SERIES);components=roots();module=SERIES/'module'/ID
    (SERIES/'reports').mkdir(exist_ok=True);(SERIES/'tex').mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        diagnostics=list(pool.map(diagnostic,components))
    (SERIES/'reports/collection_cloth_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
    # Assemble in a fresh cache; never merge stale files into the output.
    stage=SERIES/'build/collection_stage';stage.mkdir(parents=True,exist_ok=True)
    assert stage.resolve().is_relative_to((SERIES/'build').resolve())
    if any(stage.iterdir()):shutil.rmtree(stage);stage.mkdir()
    merged={};manifest=[];descriptor=None;submodules=[]
    for root in components:
        cfg=json.loads((root/'mod.json').read_text(encoding='utf8'));report=json.loads((root/cfg['validation_report']).read_text(encoding='utf8'))
        assert report.get('status','pass')=='pass' and report['final_package_sha256'].lower()==sha(root/cfg['package'])
        src=root/'module'/root.name;d=ET.parse(src/'SubModule.xml').getroot()
        if descriptor is None:descriptor=copy.deepcopy(d)
        submodules.extend(copy.deepcopy(list(d.find('SubModules'))))
        for p in src.rglob('*'):
            if not p.is_file() or p.name in ['.gitkeep','SubModule.xml']:continue
            rel=p.relative_to(src)
            if rel.parts[0]=='ModuleData' and p.suffix=='.xml':
                node=ET.parse(p).getroot()
                if p.name not in merged:merged[p.name]=ET.Element(node.tag,node.attrib)
                assert merged[p.name].tag==node.tag
                merged[p.name].extend(copy.deepcopy(list(node)))
            elif p.name=='project.mbproj':continue
            else:
                dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True)
                if dest.exists():assert dest.read_bytes()==p.read_bytes(),rel
                else:shutil.copy2(p,dest)
                manifest.append({'component':root.name,'file':rel.as_posix(),'sha256':sha(p)})
    for filename,node in merged.items():
        identifiers=[child.get('id') or child.get('name') for child in node]
        keys=[i for i in identifiers if i is not None];assert len(keys)==len(set(keys)),filename
        p=stage/'ModuleData'/filename;p.parent.mkdir(exist_ok=True)
        ET.indent(node);ET.ElementTree(node).write(p,encoding='utf-8',xml_declaration=True)
    descriptor.find('Name').set('value','Genshin Race Collection');descriptor.find('Id').set('value',ID);descriptor.find('Version').set('value',VERSION)
    sm=descriptor.find('SubModules');sm.clear();sm.extend(submodules)
    ET.indent(descriptor);ET.ElementTree(descriptor).write(stage/'SubModule.xml',encoding='utf-8',xml_declaration=True)
    shutil.copy2(components[0]/'module/EmilieRace/ModuleData/project.mbproj',stage/'ModuleData/project.mbproj')
    assert len(merged['skins.xml'])==22 and len(submodules)==22
    for component in components:
        src=component/'module'/component.name
        for filename in merged:
            if not (src/'ModuleData'/filename).exists():continue
            original=list(ET.parse(src/'ModuleData'/filename).getroot())
            assembled=list(merged[filename])
            for node in original:
                identity=node.get('id') or node.get('name')
                match=[n for n in assembled if (n.get('id') or n.get('name'))==identity]
                # Formatting whitespace is semantically irrelevant.
                def canonical(n):return (n.tag,sorted(n.attrib.items()),(n.text or '').strip(),[canonical(c) for c in n])
                assert len(match)==1 and canonical(match[0])==canonical(node),(component.name,filename,identity)
    module.parent.mkdir(exist_ok=True)
    if module.exists():
        assert module.resolve().is_relative_to((SERIES/'module').resolve());shutil.rmtree(module)
    shutil.copytree(stage,module)
    asset_index=SERIES/'reports/collection_asset_index.tsv'
    subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','guidindex',str(module/'AssetPackages'),str(asset_index)],check=True)
    assets=[line.split('\t') for line in asset_index.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    guids=[row[0] for row in assets];names=[row[2] for row in assets]
    assert len(guids)==len(set(guids)),'Duplicate asset GUID across character packages'
    assert len(names)==len(set(names)),'Duplicate asset name across character packages'
    report={'status':'pass','version':VERSION,'date':'2026-10-14','components':[p.name for p in components],'race_count':22,'submodule_count':22,'files':manifest,'module_file_hashes':{p.relative_to(module).as_posix():sha(p) for p in module.rglob('*') if p.is_file()},'xml_counts':{k:len(v) for k,v in merged.items()},'final_package_sha256':sha(module/'AssetPackages/emilie.tpac'),'game_verified':False}
    (SERIES/'reports/collection_validation.json').write_text(json.dumps(report,indent=2))
    report['unique_asset_count']=len(assets)
    (SERIES/'reports/collection_validation.json').write_text(json.dumps(report,indent=2))
    acceptance=SERIES/'reports/game_acceptance.json'
    if not acceptance.exists():acceptance.write_text(json.dumps({'version':VERSION,'status':'pending_user_test','game_launched_by_assistant':False,'emilie_existing_acceptance_preserved':True,'collection_module_loading_verified':False,'required_scenes':['module_loading','party','encyclopedia','inventory','idle','run','bow','slash','riding','cloth','lod_distances'],'old_save_dependency_migration_verified':False},indent=2))
    sources=['README.md','CHANGELOG.md','mod.json','batch_inventory.json','hair_decisions.json','reports/collection_validation.json','reports/collection_asset_index.tsv','reports/collection_cloth_diagnostics.json','reports/game_acceptance.json']
    sources.extend(p.relative_to(SERIES).as_posix() for p in module.rglob('*') if p.is_file())
    sources.extend(p.relative_to(SERIES).as_posix() for p in (SERIES/'reports').glob('*.png'))
    from cloth_simulator.pipeline import delivery_files
    for root in components:
        for p in root.rglob('*'):
            if p.is_file() and not any(x in p.relative_to(root).parts for x in ['build','dist','obj','bin','__pycache__']) and p.suffix not in ['.log','.blend1','.blend2','.pyc']:
                sources.append(p.relative_to(SERIES).as_posix())
        diagnostic_report=root/'reports/cloth_diagnostics.json'
        if diagnostic_report.exists():
            local,_=delivery_files(root,json.loads(diagnostic_report.read_text(encoding='utf8')))
            for p,entry in local:
                if p.is_relative_to(root/'build') and p.exists():
                    dest=SERIES/'reports/cloth_diagnostics'/root.name/entry
                    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
                    sources.append(dest.relative_to(SERIES).as_posix())
    shared=[p.relative_to(w).as_posix() for base in ['pmx_race_pipeline','asset_helpers','cloth_compiler','cloth_simulator'] for p in (w/'tools'/base).rglob('*') if p.is_file() and p.suffix in ['.py','.tpl','.md','.cs','.csproj','.html'] and not any(s in p.parts for s in ['obj','bin','__pycache__'])]
    shared+=['tools/race_action_sets.py','tools/package_delivery.py','tools/project_paths.py','tools/install_release.ps1']
    cfg={'id':ID,'package':f'module/{ID}/AssetPackages/emilie.tpac','validation_report':'reports/collection_validation.json','source_files':sorted(set(sources)),'shared_source_files':sorted(set(shared)),'collection_components':[p.name for p in components],'diagnostics_entry':'tools/pmx_race_pipeline/collection.py build'}
    (SERIES/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf8')
    print('COLLECTION_READY',22,flush=True)
def install():
    w=workspace_root(SERIES);module=SERIES/'module'/ID
    report=json.loads((SERIES/'reports/collection_validation.json').read_text())
    assert report['status']=='pass' and report['module_file_hashes']=={p.relative_to(module).as_posix():sha(p) for p in module.rglob('*') if p.is_file()}
    subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',str(w/'tools/install_release.ps1'),'-Mod',ID,'-Version',VERSION],check=True)
    game=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules');archive=zipfile.ZipFile(SERIES/'dist'/(ID+'_Mod.zip'))
    for p in module.rglob('*'):
        if p.is_file():assert p.read_bytes()==(game/ID/p.relative_to(module)).read_bytes()==archive.read(ID+'/'+p.relative_to(module).as_posix())
    backup=SERIES/'build/previous_installed_modules';backup.mkdir(exist_ok=True)
    removed=[]
    for root in roots():
        target=game/root.name
        if target.exists():
            assert target.resolve().parent==game.resolve() and target.name in [r.name for r in roots()]
            saved=backup/root.name
            if saved.exists():raise RuntimeError('Existing migration backup: '+str(saved))
            # Recoverable full backup before removing duplicate game modules.
            shutil.copytree(target,saved);assert {p.relative_to(target).as_posix():sha(p) for p in target.rglob('*') if p.is_file()}=={p.relative_to(saved).as_posix():sha(p) for p in saved.rglob('*') if p.is_file()}
            shutil.rmtree(target);removed.append(root.name)
    (SERIES/'reports/collection_installation.json').write_text(json.dumps({'status':'pass','installed_module':str(game/ID),'module_count':1,'removed_duplicates':removed,'backup':str(backup),'game_launched':False},indent=2))
    print('COLLECTION_INSTALLED',flush=True)
if __name__=='__main__':
    if sys.argv[1]=='build':build()
    elif sys.argv[1]=='install':install()
    else:raise ValueError('Use build or install')
