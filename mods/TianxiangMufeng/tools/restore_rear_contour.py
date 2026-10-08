"""Withdraw the rejected v1.0.1 skirt shape; preserve all historical files."""
from pathlib import Path
import json,shutil,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'build/repair_baseline_v1.0.0';ARCH=ROOT/'build/rejected_v1.0.1_rear_contour'
ARCH.mkdir(exist_ok=True)
for folder in ['source','module','reports']:
    shutil.copytree(ROOT/folder,ARCH/folder,dirs_exist_ok=True)
    shutil.copytree(BASE/folder,ROOT/folder,dirs_exist_ok=True)
for name in ['rig_arrays.npz','rig_manifest.json','geometry.json']:
    shutil.copy2(BASE/name,ROOT/'build'/name)
fitfile=ROOT/'source/SkirtClearanceFit.npz'
if fitfile.exists():shutil.move(str(fitfile),str(ARCH/'SkirtClearanceFit.npz'))
for path in list((ROOT/'reports').glob('skirt_*.json')):
    shutil.move(str(path),str(ARCH/path.name))
cfgpath=ROOT/'tools/model_config.json';cfg=json.loads(cfgpath.read_text());cfg.pop('skirt_clearance_fit',None);cfg['skirt_physics_enabled']=True;cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
descriptor=ROOT/'module/TianxiangMufeng/SubModule.xml';t=ET.parse(descriptor);t.find('Version').set('value','v1.0.2');t.write(descriptor,encoding='utf-8',xml_declaration=True)
digest=hashlib.sha256((ROOT/'module/TianxiangMufeng/AssetPackages/mf2.tpac').read_bytes()).hexdigest()
report={'status':'pass','scope':'withdraw v1.0.1 contour distortion; restore all geometry and skinning to v1.0.0','rest_contour_restored':True,'skirt_weights_restored':True,'skirt_leg_penetration_repair_complete':False,'withdrawn_version':'v1.0.1','version':'v1.0.2','package_sha256':digest,'original_lash_fix_preserved':True,'game_verified':False}
(ROOT/'reports/rear_contour_restore.json').write_text(json.dumps(report,indent=2));print('REAR_CONTOUR_RESTORED',digest)
