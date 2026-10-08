"""Validate final collection namespaces, registrations, source snapshots and bytes."""
import hashlib,json,re,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MB=Path('D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe')
AUDIT=Path('C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item_definition(node):return (node.tag,sorted(node.attrib.items()),(node.text or '').strip(),[item_definition(c) for c in node])
def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,encoding='utf-8-sig',errors='replace').stdout
manifest=json.loads((ROOT/'input/components.json').read_text(encoding='utf-8'))
module=ROOT/'module'/manifest['collection_id'];descriptor=ET.parse(module/'SubModule.xml')
assert descriptor.find('Name').get('value')=='Tianxiang Collection'
assert descriptor.find('Id').get('value')==manifest['collection_id']
assert descriptor.find('Version').get('value')==manifest['version']
assert {x.get('Id') for x in descriptor.findall('DependedModules/DependedModule')}=={'Native','SandBoxCore','Sandbox'}
assert not list(descriptor.find('SubModules'))
assert descriptor.find('Xmls/XmlNode/XmlName').get('path')=='items'
items=list(ET.parse(module/'ModuleData/items.xml').getroot());assert len(items)==24
assert len({x.get('id') for x in items})==24
assert {x.get('id') for x in items}=={i for c in manifest['components'] for i in c['items']}
guids=set();asset_names=set();meshes=set();packages=[]
for c in manifest['components']:
    package=module/'AssetPackages'/c['package_file'];digest=sha(package);assert digest==c['sha256']
    source_report=json.loads((ROOT/c['source_validation_report']).read_text(encoding='utf-8'))
    assert source_report['status']=='pass' and source_report['version']==c['version'] and source_report['final_package_sha256']==digest
    listing=run([MB,'list',package]);rows=[]
    package_guid=re.search(r'guid=([0-9a-f-]{36})',listing).group(1)
    assert package_guid not in guids;guids.add(package_guid)
    for line in listing.splitlines()[1:]:
        m=re.match(r'^(\S+)\s+(\S+)\s+([0-9a-f-]{36})\s+segs=',line)
        assert m,line
        kind,name,guid=m.groups();assert guid not in guids,(c['id'],'duplicate GUID',guid)
        assert (kind,name) not in asset_names,(c['id'],'duplicate resource',name)
        guids.add(guid);asset_names.add((kind,name));rows.append({'type':kind,'name':name,'guid':guid})
        if kind=='Metamesh':meshes.add(name)
    audit=json.loads(run([sys.executable,'-X','utf8',AUDIT,package,'--cloth-vertex-alpha']))
    assert audit['status']=='pass',audit
    (ROOT/f'reports/{c["id"]}_package_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    original=list(ET.parse(ROOT/f'sets/{c["id"]}/module/{c["id"]}/ModuleData/items.xml').getroot())
    actual=[x for x in items if x.get('id') in c['items']]
    assert [item_definition(x) for x in original]==[item_definition(x) for x in actual],c['id']
    # Source editability was verified for the upstream release; check actual copied files exist.
    assert list((ROOT/'sets'/c['id']/'source').glob('*.blend')) and list((ROOT/'sets'/c['id']/'source').glob('*.fbx'))
    assert (ROOT/'sets'/c['id']/'tex').is_dir()
    for rel in c['source_files']:assert (ROOT/rel).is_file()
    packages.append({'component':c['id'],'version':c['version'],'file':c['package_file'],'sha256':digest,'assets':len(rows),'metadata_audit':'pass','bytes_identical_to_component':True})
assert len(packages)==8 and len(meshes)==24
assert {x.get('mesh') for x in items}==meshes
assert len(list((module/'AssetPackages').glob('*.tpac')))==8
report={'status':'pass','version':manifest['version'],'check_scope':'collection assembly; upstream geometry retained byte for byte','final_package_sha256':packages[0]['sha256'],'package_hash_field_note':'primary tx5.tpac for shared installer; packages lists all eight SHA256 values','packages':packages,'sets':8,'items':24,'unique_resource_names_and_guids':True,'all_item_definitions_preserved':True,'source_snapshots_present':True,'game_test_verified':False,'user_confirmed_components':[{'id':'TianxiangXuezhi','version':'v1.0.1','feedback':'第七套我已验证，没问题。','date':'2026-10-08'}],'limitations':'Collection loading is not game-tested. Disable all eight standalone modules when enabling this collection to avoid duplicate item IDs and resources.'}
(ROOT/'reports/release_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
files=['README.md','mod.json','input/components.json','tools/build_collection.py','tools/verify_collection.py','reports/release_validation.json']
files.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'tools').glob('*.py'))
if (ROOT/'reports/grouped_paths.json').is_file():files.append('reports/grouped_paths.json')
for name in ['grouping_preservation.json','grouped_source_validation.json']:
    if (ROOT/'reports'/name).is_file():files.append('reports/'+name)
files.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'reports').glob('*_package_audit.json'))
files.extend(rel for c in manifest['components'] for rel in c['source_files'])
# Include runtime packages in editable archive once, so assembly is reproducible without rebuilding models.
files.extend(p.relative_to(ROOT).as_posix() for p in module.rglob('*') if p.is_file() and p.name!='.gitkeep')
config={'id':manifest['collection_id'],'source_files':sorted(set(files)),'package':f'module/{manifest["collection_id"]}/AssetPackages/{packages[0]["file"]}','validation_report':'reports/release_validation.json'}
(ROOT/'mod.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
print('COLLECTION_VERIFIED',len(packages),'packages',len(items),'items',len(asset_names),'unique resources')
