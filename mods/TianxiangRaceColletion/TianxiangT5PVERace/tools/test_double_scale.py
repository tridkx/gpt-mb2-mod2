"""Publish a scale-only 2x parameter test; preserve v0.1.0 resources."""
import json,hashlib,shutil,zipfile
from pathlib import Path
from lxml import etree as ET
from verify_registration import canonical,validate_registration
R=Path(__file__).resolve().parents[1];M=R/'module/TianxiangT5PVERace'
cfgpath=R/'tools/model_config.json';cfg=json.loads(cfgpath.read_text())
assert cfg['version']=='v0.1.0' and cfg['skin_min_scale']==1.0,'One-time test migration; do not apply repeatedly'
history=R/'reports/history/v0.1.0';history.mkdir(parents=True,exist_ok=True)
for file in ['release_validation.json','registration_validation.json']:
    dst=history/file;assert not dst.exists();shutil.copy2(R/'reports'/file,dst)
shutil.copy2(cfgpath,history/'model_config.json')
old=json.loads((history/'release_validation.json').read_text());assert old['status']=='pass'
cfg.update(version='v0.1.1',skin_min_scale=2.0,scale_test=True,scale_baseline_version='v0.1.0')
cfgpath.write_text(json.dumps(cfg,indent=2),encoding='utf8')
parser=ET.XMLParser(remove_blank_text=True)
for relative in ['ModuleData/skins.xml','SubModule.xml']:
    path=M/relative;tree=ET.parse(str(path),parser)
    if relative.endswith('skins.xml'):
        for row in tree.findall('race/skin'):row.set('min_scale','2.0')
    else:tree.find('Version').set('value',cfg['version'])
    tree.write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
registration=validate_registration(R)
sha=lambda b:hashlib.sha256(b).hexdigest()
changed=[]
with zipfile.ZipFile(R/'dist/TianxiangT5PVERace_Mod.zip') as z:
    assert ET.fromstring(z.read('TianxiangT5PVERace/SubModule.xml')).find('Version').get('value')=='v0.1.0'
    for path in M.rglob('*'):
        if not path.is_file():continue
        relative=path.relative_to(M).as_posix();before=z.read('TianxiangT5PVERace/'+relative);after=path.read_bytes()
        if before==after:continue
        changed.append(relative)
        previous=ET.fromstring(before,parser);current=ET.fromstring(after,parser)
        if relative=='ModuleData/skins.xml':
            for row in previous.findall('race/skin'):
                assert float(row.get('min_scale'))==1;row.set('min_scale','2.0')
        elif relative=='SubModule.xml':previous.find('Version').set('value','v0.1.1')
        else:raise AssertionError(relative)
        assert canonical(previous)==canonical(current),relative
assert set(changed)=={'ModuleData/skins.xml','SubModule.xml'}
report=dict(old)
report.update(version='v0.1.1',date='2026-10-12',check_scope='scale_only_test_against_v0.1.0_delivery',registration=registration,game_test_verified=False,
 baseline_package_sha256=old['final_package_sha256'],baseline_reason='Scale test preserves exact v0.1.0 TPAC and runtime DLL',
 scale_test={'previous_min_scale':1.0,'new_min_scale':2.0,'parameter_ratio':2.0,'changed_module_files':sorted(changed),'all_skin_variants':10,'runtime_effect_verified':False,'expected_scale_same_body_key':0.9031746*2},
 module_file_sha256={p.relative_to(M).as_posix():sha(p.read_bytes()) for p in M.rglob('*') if p.is_file()})
assert sha((M/'AssetPackages/txt5pve.tpac').read_bytes())==old['final_package_sha256']
(R/'reports/release_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
manifest=json.loads((R/'mod.json').read_text());manifest['source_files']=sorted(set(manifest['source_files']+['tools/test_double_scale.py','tools/diagnose_scale.py','reports/height_diagnosis_2026-10-12.json']+[p.relative_to(R).as_posix() for p in history.iterdir() if p.is_file()]))
(R/'mod.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps(report['scale_test'],ensure_ascii=False))
