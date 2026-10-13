"""Assemble a single module without rewriting accepted character resources."""
from pathlib import Path
import json,hashlib,copy,shutil,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];C=R.parent;ID='TianxiangRaceCollection';VERSION='v0.1.0'
M=R/'module'/ID
(M/'ModuleData').mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(node):
    return (node.tag,tuple(sorted(node.attrib.items())),(node.text or '').strip(),tuple(canonical(n) for n in node))
def write(p,node):
    E.indent(node,space='  ');E.ElementTree(node).write(p,encoding='utf-8',xml_declaration=True)
names=json.loads((R/'tools/components.json').read_text())
roots={file:E.Element(tag) for file,tag in [('skins','skins'),('action_sets','action_sets'),('monsters','Monsters'),('cloth_bodies','bodies'),('test_troop','NPCCharacters')]}
identities={file:set() for file in roots};descriptors=[];components=[];expected={};outputs={}
for ident in names:
    P=C/ident;S=P/'module'/ident;descriptor=E.parse(S/'SubModule.xml').getroot();descriptors.append(descriptor)
    cfg=json.loads((P/'mod.json').read_text());validation=json.loads((P/cfg['validation_report']).read_text())
    assert validation['status']=='pass' and validation['final_package_sha256']==sha(P/cfg['package'])
    assert validation['version']==descriptor.find('Version').get('value')
    copied=[]
    for folder in ['AssetPackages','bin']:
        for p in (S/folder).rglob('*'):
            if not p.is_file():continue
            dest=M/p.relative_to(S);dest.parent.mkdir(parents=True,exist_ok=True)
            relative=dest.relative_to(M).as_posix()
            assert relative not in outputs or outputs[relative]==sha(p),'Conflicting component output filename'
            outputs[relative]=sha(p)
            shutil.copy2(p,dest);assert sha(dest)==sha(p)
            copied.append(dict(path=dest.relative_to(M).as_posix(),sha256=sha(p)))
    for file in roots:
        p=S/'ModuleData'/(file+'.xml')
        if not p.exists():continue
        original=E.parse(p).getroot();assert original.tag==roots[file].tag
        for child in original:
            key=child.get('id') or child.get('name')
            assert key and key not in identities[file],(file,key)
            identities[file].add(key);roots[file].append(copy.deepcopy(child));expected[(file,key)]=canonical(child)
    components.append(dict(id=ident,version=validation['version'],package_sha256=validation['final_package_sha256'],copied_files=copied))
for file,node in roots.items():write(M/'ModuleData'/(file+'.xml'),node)
project=E.Element('base',type='solution')
for ident,file,kind in [('soln_skins','skins','skin'),('soln_action_sets','action_sets','action_set'),('soln_monsters','monsters','monster')]:
    E.SubElement(project,'file',id=ident,name='ModuleData/'+file+'.xml',type=kind)
write(M/'ModuleData/project.mbproj',project)
sub=copy.deepcopy(descriptors[0])
sub.find('Name').set('value','Tianxiang Race Collection');sub.find('Id').set('value',ID);sub.find('Version').set('value',VERSION)
submodules=sub.find('SubModules');submodules.clear()
for descriptor in descriptors:
    for node in descriptor.findall('SubModules/SubModule'):submodules.append(copy.deepcopy(node))
deps=sub.find('DependedModules');deps.clear();seen=set()
for descriptor in descriptors:
    for node in descriptor.findall('DependedModules/DependedModule'):
        key=node.get('Id')
        if key not in seen:deps.append(copy.deepcopy(node));seen.add(key)
xmls=sub.find('Xmls');xmls.clear();loaded={}
for descriptor in descriptors:
    for node in descriptor.findall('Xmls/XmlNode'):
        ref=node.find('XmlName');key=(ref.get('id'),ref.get('path'))
        assert (M/'ModuleData'/(key[1]+'.xml')).is_file()
        if key not in loaded:loaded[key]=copy.deepcopy(node)
        else:
            types=loaded[key].find('IncludedGameTypes');values={t.get('value') for t in types}
            for t in node.find('IncludedGameTypes'):
                if t.get('value') not in values:types.append(copy.deepcopy(t));values.add(t.get('value'))
for node in loaded.values():xmls.append(node)
write(M/'SubModule.xml',sub)
for file in roots:
    for node in E.parse(M/'ModuleData'/(file+'.xml')).getroot():
        key=node.get('id') or node.get('name');assert canonical(node)==expected[(file,key)]
assert len(identities['skins'])==9
assert len({s.find('DLLName').get('value') for s in submodules})==9
for component in components:
    for item in component['copied_files']:assert sha(M/item['path'])==item['sha256']
manifest=dict(id=ID,version=VERSION,components=components,registration_counts={k:len(v) for k,v in identities.items()})
(R/'source/manifest.json').write_text(json.dumps(manifest,indent=2))
report=dict(status='pass',version=VERSION,check_scope='Nine component resource packages and runtime assemblies copied byte-for-byte; merged XML child structures and all original identifiers preserved',
    final_package_sha256=components[0]['package_sha256'],components=components,registration_counts=manifest['registration_counts'],
    preserved_runtime_submodules=9,game_test_verified=False,launcher_settings_modified=False,
    module_file_sha256={p.relative_to(M).as_posix():sha(p) for p in M.rglob('*') if p.is_file()})
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
files=[p.relative_to(R).as_posix() for folder in ['tools','source','reports'] for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files+=['README.md','CHANGELOG.md','.gitignore','.gitattributes','mod.json']
(R/'mod.json').write_text(json.dumps(dict(id=ID,source_files=sorted(set(files)),shared_source_files=[],
    package=components[0]['copied_files'][0]['path'],validation_report='reports/release_validation.json'),indent=2))
# The common installer expects package paths relative to this project.
cfg=json.loads((R/'mod.json').read_text());cfg['package']='module/'+ID+'/AssetPackages/'+Path(json.loads((C/names[0]/'mod.json').read_text())['package']).name
(R/'mod.json').write_text(json.dumps(cfg,indent=2))
print('COLLECTION_READY',manifest['registration_counts'],'runtime_submodules',len(submodules))
