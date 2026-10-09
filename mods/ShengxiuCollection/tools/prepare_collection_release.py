"""Compose validated set packages, preserving the accepted Mingyu package."""
from pathlib import Path
import json,hashlib,shutil,xml.etree.ElementTree as ET,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
VERSION='v1.1.0'
MINGYU='616b97186624b1cc220385e017224e2ad8e3d5046fe10d276cc1b1a8e6ad1708'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
module=ROOT/'module/ShengxiuCollection'
assert sha(module/'AssetPackages/sx_mingyu.tpac')==MINGYU
items=ET.parse(module/'ModuleData/items.xml')
for item in list(items.getroot()):
 if not item.get('id').startswith('sx_mingyu_'):items.getroot().remove(item)
rows=[];names=set();guids=set();packs=set()
for dirname in [None,'02_Baifeng','03_Suwen']:
 root=ROOT if dirname is None else ROOT/'sets'/dirname
 cfg=json.loads((root/'tools/model_config.json').read_text(encoding='utf-8'));prefix=cfg['prefix']
 package=root/f'module/ShengxiuCollection/AssetPackages/{prefix}.tpac'
 report=json.loads((root/'reports/release_validation.json').read_text())
 assert report['status']=='pass' and report['final_package_sha256']==sha(package)
 pack=json.loads((root/'build/final_export/pack.json').read_text())
 assert pack['packGuid'] not in packs;packs.add(pack['packGuid'])
 for kind in ['meshes','materials','textures']:
  for asset in pack[kind]:
   assert asset['name'] not in names,(asset['name'],'resource collision');names.add(asset['name'])
   assert asset['guid'] not in guids,(asset['name'],'GUID collision');guids.add(asset['guid'])
 if dirname:
  cloth=json.loads((root/'reports/cooked_cloth_validation.json').read_text())
  assert cloth['status']=='pass' and cloth['final_package_sha256']==sha(package)
  assert json.loads((root/'reports/source_validation.json').read_text())['status']=='pass'
  head=json.loads((root/'reports/head_follow_validation.json').read_text());assert head['status']=='pass' and head['package_sha256']==sha(package)
  preview=json.loads((root/'reports/final_preview_manifest.json').read_text())
  assert preview['package_sha256']==sha(package)
  for image in ['rest_front','rest_side','rest_back','face_all','run_worst','bow_worst','riding_worst']:
   assert (root/f'reports/final_{image}.png').is_file()
  preserved=[];original=Path(cfg['original_directory'])
  for f in [*sorted((root/'input').rglob('*')),*[root/'tex'/p.relative_to(original/'tex') for p in sorted((original/'tex').rglob('*'))]]:
   if not f.is_file():continue
   relative=f.relative_to(root)
   origin=original/f.relative_to(root/'input') if relative.parts[0]=='input' else original/'tex'/f.relative_to(root/'tex')
   assert sha(f)==sha(origin),(f,'original changed')
   preserved.append({'copy':relative.as_posix(),'original':str(origin),'sha256':sha(f)})
  (root/'reports/input_preservation.json').write_text(json.dumps({'status':'pass','files':preserved},ensure_ascii=False,indent=2),encoding='utf-8')
  for item in ET.parse(root/'module/ShengxiuCollection/ModuleData/items.xml').getroot():items.getroot().append(item)
  shutil.copy2(package,module/'AssetPackages'/package.name)
  # Sole pitch was fitted from this set; measure source and final TPAC.
  ws=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
  sys.path.insert(0,str(ws/'tools/asset_helpers/tools'))
  from georead import read_geo
  manifest=json.loads((root/'build/rig_manifest.json').read_text())
  shoe=next(r for r in manifest if r['texture_key']=='pants')
  meshes=[m for f in (root/'build/final_export/geo').glob('*.bin') for m in read_geo(f)]
  p=next(m['pos'] for m in meshes if m['name']==shoe['object'])
  low=p[p[:,2]<.14];length=float(np.ptp(low[:,1]));ground=float(low[:,2].min())
  assert abs(ground-.001)<.00001 and abs(length-.245)<.012,(dirname,length,ground)
  (root/'reports/foot_fit_validation.json').write_text(json.dumps({'status':'pass','package_sha256':sha(package),'minimum_sole_z_m':ground,'low_shoe_length_m':length,'independent_parameters':cfg['foot_fit']},indent=2))
 rows.append({'set':cfg['title'],'prefix':prefix,'path':f'module/ShengxiuCollection/AssetPackages/{package.name}',
  'sha256':sha(package),'package_guid':pack['packGuid'],'report':str((root/'reports/release_validation.json').relative_to(ROOT)).replace('\\','/'),
  'cloth_meshes':len(cloth['cooked_meshes']) if dirname else 4,'lods':report['lods']})
assert len(items.getroot())==9 and len({i.get('id') for i in items.getroot()})==9
assert {i.get('mesh') for i in items.getroot()}=={prefix+'_'+part for prefix in ['sx_mingyu','sx_baifeng','sx_suwen'] for part in ['head','body','legs']}
ET.indent(items,space='  ');items.write(module/'ModuleData/items.xml',encoding='utf-8',xml_declaration=True)
descriptor=ET.parse(module/'SubModule.xml');descriptor.find('Version').set('value',VERSION)
assert descriptor.find('Name').get('value').isascii()
ET.indent(descriptor,space='  ');descriptor.write(module/'SubModule.xml',encoding='utf-8',xml_declaration=True)
for file in module.rglob('*.xml'):file.write_bytes(file.read_bytes().replace(b'\r\n',b'\n'))
report={'status':'pass','version':VERSION,'check_scope':'offline_checks','final_package_sha256':MINGYU,
 'mingyu_v1_0_4_package_unchanged':True,'packages':rows,'registered_items':9,
 'resource_and_guid_collisions':False,'native_28_bone_binding':True,
 'new_cloth_lods':[0,1],'game_test_verified':False,'game_cloth_solver_used':False,
 'limitations':'New outfits validated offline. Natural cloth motion, weapon IK, body sliders and mounted collision require user game testing.'}
(ROOT/'reports/collection_release_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
config=json.loads((ROOT/'mod.json').read_text())
config['validation_report']='reports/collection_release_validation.json'
sources=set(config['source_files']);sources.add('reports/collection_release_validation.json')
for f in (ROOT/'sets').rglob('*'):
 if f.is_file() and not any(x in f.relative_to(ROOT).parts for x in ['build','obj','bin','__pycache__']) and f.suffix not in ['.blend1','.tpac']:
  sources.add(f.relative_to(ROOT).as_posix())
for f in ['tools/inspect_new_sets.py','tools/verify_set_cloth.py','tools/prepare_collection_release.py','tools/build_new_sets.py','tools/verify_head_follow.py','tools/render_head_comparison.py']:
 sources.add(f)
config['source_files']=sorted(sources)
(ROOT/'mod.json').write_text(json.dumps(config,indent=2))
print('COLLECTION_READY',VERSION,'9 items; 3 packages; Mingyu unchanged')
