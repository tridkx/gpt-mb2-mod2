"""Publish a scale-only change against an exact prior delivery."""
import argparse,json,hashlib,shutil,zipfile
from pathlib import Path
from lxml import etree as ET
from verify_registration import canonical,validate_registration
R=Path(__file__).resolve().parents[1];M=R/'module/TianxiangT5PVERace'
parser=argparse.ArgumentParser();parser.add_argument('--version',required=True);parser.add_argument('--min-scale',type=float,required=True);args=parser.parse_args()
assert args.min_scale>0
cfgpath=R/'tools/model_config.json';cfg=json.loads(cfgpath.read_text());baseline=cfg['version'];previous_scale=cfg['skin_min_scale'];assert baseline!=args.version
history=R/'reports/history'/baseline;history.mkdir(parents=True,exist_ok=True)
for filename in ['release_validation.json','registration_validation.json']:
    destination=history/filename;assert not destination.exists();shutil.copy2(R/'reports'/filename,destination)
shutil.copy2(cfgpath,history/'model_config.json');old=json.loads((history/'release_validation.json').read_text());assert old['status']=='pass'
cfg.update(version=args.version,skin_min_scale=args.min_scale,scale_test=False,scale_baseline_version=baseline,
 scale_calibration={'target_runtime_scale':1.0,'baseline_parameter':1.0,'observed_baseline_ui_scale':0.9031746,'observed_double_parameter_ui_scale':1.80634916,'scope':'Male character creation, same body parameters; final battlefield/female scale pending'})
cfgpath.write_text(json.dumps(cfg,indent=2),encoding='utf8');xmlparser=ET.XMLParser(remove_blank_text=True)
for relative in ['ModuleData/skins.xml','SubModule.xml']:
    path=M/relative;tree=ET.parse(str(path),xmlparser)
    if relative.endswith('skins.xml'):
        for row in tree.findall('race/skin'):row.set('min_scale',str(args.min_scale))
    else:tree.find('Version').set('value',args.version)
    tree.write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)
registration=validate_registration(R);sha=lambda b:hashlib.sha256(b).hexdigest();changed=[]
with zipfile.ZipFile(R/'dist/TianxiangT5PVERace_Mod.zip') as z:
    assert ET.fromstring(z.read('TianxiangT5PVERace/SubModule.xml')).find('Version').get('value')==baseline
    for path in M.rglob('*'):
        if not path.is_file():continue
        relative=path.relative_to(M).as_posix();before=z.read('TianxiangT5PVERace/'+relative);after=path.read_bytes()
        if before==after:continue
        changed.append(relative);previous=ET.fromstring(before,xmlparser);current=ET.fromstring(after,xmlparser)
        if relative=='ModuleData/skins.xml':
            for row in previous.findall('race/skin'):
                assert float(row.get('min_scale'))==previous_scale;row.set('min_scale',str(args.min_scale))
        elif relative=='SubModule.xml':previous.find('Version').set('value',args.version)
        else:raise AssertionError(relative)
        assert canonical(previous)==canonical(current),relative
assert set(changed)=={'ModuleData/skins.xml','SubModule.xml'}
report=dict(old);report.pop('scale_test',None)
report.update(version=args.version,date='2026-10-12',check_scope='scale_only_source_size_calibration_against_prior_delivery',registration=registration,game_test_verified=False,
 baseline_package_sha256=old['final_package_sha256'],baseline_reason='Uniform display scale calibration; exact assets preserved',
 scale_calibration=dict(cfg['scale_calibration'],previous_min_scale=previous_scale,new_min_scale=args.min_scale,expected_ui_scale_same_body_key=args.min_scale*.9031746,changed_module_files=sorted(changed),final_runtime_verified=False),
 module_file_sha256={p.relative_to(M).as_posix():sha(p.read_bytes()) for p in M.rglob('*') if p.is_file()})
assert sha((M/'AssetPackages/txt5pve.tpac').read_bytes())==old['final_package_sha256']
(R/'reports/release_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
manifest=json.loads((R/'mod.json').read_text());manifest['source_files']=sorted(set(manifest['source_files']+['tools/publish_scale.py','reports/scale_parameter_acceptance.json']+[p.relative_to(R).as_posix() for p in history.iterdir() if p.is_file()]))
(R/'mod.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps(report['scale_calibration'],ensure_ascii=False))
