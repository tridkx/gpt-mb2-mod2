"""Validate two independent sets and assemble the cumulative v1.1.0 module."""
from pathlib import Path
import json,hashlib,shutil,zipfile,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
SETS=['01_YunhaiNiezong','02_XuanxuQingjing'];VERSION='v1.1.0'
BASELINE='f163e4d104e674da22fe5513e751f71ffa9ce15abf2367e253234165a98d2323'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
packages=[];all_items=[];names=set();guids=set();inventories=[]
for setname,prefix in zip(SETS,['zw_yunhai','zw_xuanxu']):
 folder=ROOT/'sets'/setname;module=folder/'module/ZhenwuCollection';package=module/'AssetPackages'/(prefix+'.tpac');h=sha(package)
 release=json.loads((folder/'reports/release_validation.json').read_text())
 assert release['status']=='pass' and release['final_package_sha256']==h
 for name in ['source_validation','native_provenance','detail_validation','package_audit','eye_uv_validation']:
  report=json.loads((folder/'reports'/(name+'.json')).read_text())
  assert report['status']=='pass',(setname,name)
  if 'final_package_sha256' in report:assert report['final_package_sha256']==h,(setname,name)
 preview=json.loads((folder/'reports/final_preview_manifest.json').read_text())
 assert preview['package_sha256']==h and preview.get('visually_reviewed') is True
 for p in preview['previews']:assert (folder/p['path']).is_file()
 readback=ROOT/'build/readback'/setname
 subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(package),str(readback),'0'],check=True,stdout=subprocess.DEVNULL)
 inventory=json.loads((readback/'pack.json').read_text())
 assert inventory['packGuid'] not in guids;guids.add(inventory['packGuid'])
 assets=sum([inventory.get(k,[]) for k in ['meshes','materials','textures']],[])
 assert len(assets)==23
 for asset in assets:
  assert asset['name'].startswith(prefix+'_') and asset['name'] not in names and asset['guid'] not in guids
  names.add(asset['name']);guids.add(asset['guid'])
 inventories.append({'set':setname,'package_guid':inventory['packGuid'],'asset_count':len(assets),'assets':[{'name':a['name'],'guid':a['guid']} for a in assets]})
 packages.append({'set':setname,'file':'module/ZhenwuCollection/AssetPackages/'+package.name,'sha256':h,'offline_status':'pass','user_acceptance':'accepted_v1.0.0' if setname==SETS[0] else 'pending'})
 all_items.extend(list(ET.parse(module/'ModuleData/items.xml').getroot()))
# First accepted assets and editable model must remain exactly as delivered.
assert packages[0]['sha256']==BASELINE
accept=json.loads((ROOT/'reports/acceptance_v1.0.0.json').read_text(encoding='utf8'))
assert accept['status']=='accepted_by_user' and accept['accepted_package_sha256']==BASELINE
oldmod=ROOT/'dist/ZhenwuCollection_v1.0.0_Mod.zip'
oldsource=ROOT/'dist/ZhenwuCollection_v1.0.0_Source.zip'
if not oldmod.exists():oldmod=ROOT/'dist/ZhenwuCollection_Mod.zip'
if not oldsource.exists():oldsource=ROOT/'dist/ZhenwuCollection_Source.zip'
with zipfile.ZipFile(oldmod) as z:
 assert z.read('ZhenwuCollection/AssetPackages/zw_yunhai.tpac')==(ROOT/packages[0]['file']).read_bytes()
 assert ET.tostring(ET.fromstring(z.read('ZhenwuCollection/ModuleData/items.xml')))==ET.tostring(ET.parse(ROOT/'sets'/SETS[0]/'module/ZhenwuCollection/ModuleData/items.xml').getroot())
with zipfile.ZipFile(oldsource) as z:
 for rel in ['source/ZhenwuYunhai_Rigged.blend','source/ZhenwuYunhai_Rigged.fbx',*['tex/'+p.name for p in (ROOT/'sets'/SETS[0]/'tex').glob('*.png')]]:
  path='sets/'+SETS[0]+'/'+rel
  assert z.read(path)==(ROOT/path).read_bytes(),path
module=ROOT/'module/ZhenwuCollection';(module/'AssetPackages').mkdir(parents=True,exist_ok=True)
for pkg in packages:
 shutil.copy2(ROOT/'sets'/pkg['set']/'module/ZhenwuCollection/AssetPackages'/Path(pkg['file']).name,ROOT/pkg['file'])
 assert sha(ROOT/pkg['file'])==pkg['sha256']
shutil.copy2(ROOT/'sets'/SETS[1]/'module/ZhenwuCollection/SubModule.xml',module/'SubModule.xml')
items=ET.Element('Items');items.extend(all_items);ids=[i.get('id') for i in items];assert len(ids)==6 and len(set(ids))==6
assert {i.get('mesh') for i in items}=={a['name'] for inv in inventories for a in inv['assets'] if a['name'].endswith(('_head','_body','_legs'))}
ET.indent(items,space='  ');ET.ElementTree(items).write(module/'ModuleData/items.xml',encoding='utf-8',xml_declaration=True)
assert ET.parse(module/'SubModule.xml').find('Version').get('value')==VERSION
report={'version':VERSION,'status':'pass','check_scope':'offline checks and cumulative module consistency','final_package_sha256':packages[-1]['sha256'],'baseline_package_sha256':BASELINE,'packages':packages,'asset_inventory':inventories,'resource_name_and_guid_collisions':False,'first_set_assets_and_source_unchanged':True,'item_count':6,'included_sets':SETS,'editable_sources_verified':True,'all_lod_motion_and_seam_normals_verified':True,'second_set_user_acceptance':'pending','game_test_verified':False,'game_cloth_solver_used':False,'limitations':'User accepted first set v1.0.0 without reporting individual motions. Second-set in-game cloth, IK, body sliders and horse collision await user testing.'}
(ROOT/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
files=['README.md','mod.json']
for folder in ['tools','reports','module','sets']:
 for p in sorted((ROOT/folder).rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(ROOT)
  if any(v in ['build','dist','obj','bin','__pycache__'] for v in rel.parts):continue
  if p.suffix in ['.pyc','.blend1','.blend2','.log'] or p.name=='.gitkeep':continue
  if p.name.startswith('installation_validation'):continue
  if 'module' in rel.parts and p.suffix=='.tpac':continue
  if 'reports' in rel.parts and p.suffix=='.png' and not p.name.startswith('final_'):continue
  files.append(rel.as_posix())
config={'id':'ZhenwuCollection','source_files':sorted(set(files)),'package':packages[-1]['file'],'packages':[p['file'] for p in packages],'validation_report':'reports/release_validation.json','included_sets':SETS,'eighth_set_variant':'PVP'}
(ROOT/'mod.json').write_text(json.dumps(config,indent=2))
print('COLLECTION_DELIVERY_READY',VERSION,len(config['source_files']),'source files',len(names),'unique assets')
