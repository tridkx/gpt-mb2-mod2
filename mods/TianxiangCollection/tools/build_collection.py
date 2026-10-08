"""Assemble released equipment without changing its geometry or resource identities."""
import argparse,copy,hashlib,json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def project_path(workspace,ident):
    a=workspace/'mods'/ident;b=workspace/'mods/TianxiangCollection/sets'/ident
    return a if (a/'mod.json').is_file() else b
ID='TianxiangCollection'
COMPONENTS=['TianxiangT5','TianxiangRenqiu','TianxiangMufeng','TianxiangQingmei','TianxiangMuyu','TianxiangFangzi','TianxiangSuimeng','TianxiangXuezhi']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_xml(tree,path):
    ET.indent(tree,space='  ');tree.write(path,encoding='utf-8',xml_declaration=True)
def build(workspace):
    module=ROOT/'module'/ID;items=ET.Element('Items');manifest=[];seen=set();dependencies=set()
    for ident in COMPONENTS:
        src=project_path(workspace,ident);config=json.loads((src/'mod.json').read_text(encoding='utf-8'))
        descriptor=ET.parse(src/f'module/{ident}/SubModule.xml')
        version=descriptor.find('Version').get('value')
        report=json.loads((src/config['validation_report']).read_text(encoding='utf-8'))
        package=src/config['package']
        assert report['status']=='pass' and report['version']==version
        assert sha(package)==report['final_package_sha256'],ident
        dependencies.update(x.get('Id') for x in descriptor.findall('DependedModules/DependedModule'))
        filename=package.name;target=module/'AssetPackages'/filename
        assert not any(x['package_file']==filename for x in manifest)
        shutil.copy2(package,target)
        rows=list(ET.parse(src/f'module/{ident}/ModuleData/items.xml').getroot())
        assert len(rows)==3
        for item in rows:
            assert item.get('id') not in seen;seen.add(item.get('id'));items.append(copy.deepcopy(item))
        # Preserve each released editable-source layout, including adjacent source/tex.
        snapshot=ROOT/'sets'/ident
        files=set(config['source_files'])|{'mod.json',f'module/{ident}/SubModule.xml',f'module/{ident}/ModuleData/items.xml'}
        files.update(p.relative_to(src).as_posix() for p in (src/'tex').rglob('*') if p.is_file() and p.name!='.gitkeep')
        for rel in sorted(files):
            path=(src/rel).resolve();assert path.is_relative_to(src.resolve()) and path.is_file()
            dest=snapshot/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if path!=dest.resolve():shutil.copy2(path,dest)
        manifest.append({'id':ident,'version':version,'package_file':filename,'sha256':sha(target),'items':[x.get('id') for x in rows],'source_validation_report':f'sets/{ident}/{config["validation_report"]}','source_files':[f'sets/{ident}/{r}' for r in sorted(files)]})
    assert dependencies=={'Native','SandBoxCore','Sandbox'}
    tree=ET.parse(project_path(workspace,'TianxiangXuezhi')/'module/TianxiangXuezhi/SubModule.xml')
    tree.find('Name').set('value','Tianxiang Collection');tree.find('Id').set('value',ID);tree.find('Version').set('value','v1.0.0')
    write_xml(tree,module/'SubModule.xml');write_xml(ET.ElementTree(items),module/'ModuleData/items.xml')
    (ROOT/'input/components.json').write_text(json.dumps({'collection_id':ID,'version':'v1.0.0','components':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    print('COLLECTION_BUILT',len(manifest),'sets',len(items),'items')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-workspace',type=Path,default=ROOT.parents[1])
    build(parser.parse_args().input_workspace.resolve())
