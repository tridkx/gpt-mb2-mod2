"""Verify all eight sets, preserve the accepted v1.2.0 baseline, assemble v1.3.0."""
from pathlib import Path
import json,hashlib,shutil,zipfile,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];VERSION='v1.3.0'
SETS=['01_YunhaiNiezong','02_XuanxuQingjing','03_HuashuiWeiming','04_DanyunWeiyu','05_FuyuChongyun','06_XuanjiKongmeng','07_YimoCangming','08_ShenjiTaolue']
ACCEPTED=['v1.0.0','v1.1.0','v1.2.0']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def structural(e):return (e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(structural(c) for c in e))
packages=[];all_items=[];names=set();guids=set();inventories=[]
for index,setname in enumerate(SETS):
 folder=ROOT/'sets'/setname;cfg=json.loads((folder/'tools/model_config.json').read_text(encoding='utf8'));prefix=cfg['prefix']
 module=folder/'module/ZhenwuCollection';package=module/'AssetPackages'/(prefix+'.tpac');h=sha(package)
 release=json.loads((folder/'reports/release_validation.json').read_text())
 assert release['status']=='pass' and release['final_package_sha256']==h
 for name in ['source_validation','native_provenance','detail_validation','package_audit','eye_uv_validation']:
  report=json.loads((folder/'reports'/(name+'.json')).read_text());assert report['status']=='pass',(setname,name)
  if 'final_package_sha256' in report:assert report['final_package_sha256']==h,(setname,name)
 if index>=4:
  cloth=json.loads((folder/'reports/cooked_cloth_validation.json').read_text());assert cloth['status']=='pass' and cloth['final_package_sha256']==h and cloth['enabled_lods']==[0,1]
 preview=json.loads((folder/'reports/final_preview_manifest.json').read_text())
 assert preview['package_sha256']==h and preview.get('visually_reviewed') is True
 for row in preview['previews']:assert (folder/row['path']).is_file()
 acceptance='pending'
 if index<3:
  record=json.loads((ROOT/'reports'/('acceptance_'+ACCEPTED[index]+'.json')).read_text(encoding='utf8'))
  assert record['status']=='accepted_by_user' and record['accepted_package_sha256']==h
  acceptance='accepted_'+ACCEPTED[index]
 if index==7:
  assert cfg['selected_variant']=='PVP' and cfg['selected_source_file']=='model_PVP.fbx'
  assert sha(folder/'input/model.fbx')==sha(Path(cfg['original_directory'])/'model_PVP.fbx')
  assert not any('PVE' in p.name.upper() for p in (folder/'tex').glob('*'))
 readback=ROOT/'build/readback'/setname
 subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(package),str(readback),'0'],check=True,stdout=subprocess.DEVNULL)
 inventory=json.loads((readback/'pack.json').read_text());assert inventory['packGuid'] not in guids;guids.add(inventory['packGuid'])
 assets=sum([inventory.get(k,[]) for k in ['meshes','materials','textures']],[])
 assert len(assets)==3+len(cfg['textures'])+len(cfg['textures'])+2
 for asset in assets:
  assert asset['name'].startswith(prefix+'_') and asset['name'] not in names and asset['guid'] not in guids
  names.add(asset['name']);guids.add(asset['guid'])
 inventories.append({'set':setname,'package_guid':inventory['packGuid'],'asset_count':len(assets),'assets':[{'name':a['name'],'guid':a['guid']} for a in assets]})
 packages.append({'set':setname,'file':'module/ZhenwuCollection/AssetPackages/'+package.name,'sha256':h,'offline_status':'pass','user_acceptance':acceptance})
 all_items.extend(list(ET.parse(module/'ModuleData/items.xml').getroot()))
oldmod=ROOT/'dist/ZhenwuCollection_v1.2.0_Mod.zip';oldsource=ROOT/'dist/ZhenwuCollection_v1.2.0_Source.zip'
if not oldmod.exists():oldmod=ROOT/'dist/ZhenwuCollection_Mod.zip'
if not oldsource.exists():oldsource=ROOT/'dist/ZhenwuCollection_Source.zip'
with zipfile.ZipFile(oldmod) as z:
 for pkg in packages[:3]:assert z.read('ZhenwuCollection/AssetPackages/'+Path(pkg['file']).name)==(ROOT/pkg['file']).read_bytes()
 assert [structural(i) for i in ET.fromstring(z.read('ZhenwuCollection/ModuleData/items.xml'))]==[structural(i) for i in all_items[:9]]
with zipfile.ZipFile(oldsource) as z:
 for setname in SETS[:3]:
  folder=ROOT/'sets'/setname
  for p in [*sorted((folder/'source').glob('*.blend')),*sorted((folder/'source').glob('*.fbx')),*sorted((folder/'tex').glob('*.png'))]:assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes(),str(p)
module=ROOT/'module/ZhenwuCollection';(module/'AssetPackages').mkdir(parents=True,exist_ok=True)
for pkg in packages:
 shutil.copy2(ROOT/'sets'/pkg['set']/'module/ZhenwuCollection/AssetPackages'/Path(pkg['file']).name,ROOT/pkg['file']);assert sha(ROOT/pkg['file'])==pkg['sha256']
shutil.copy2(ROOT/'sets'/SETS[-1]/'module/ZhenwuCollection/SubModule.xml',module/'SubModule.xml')
items=ET.Element('Items');items.extend(all_items);ids=[i.get('id') for i in items];assert len(ids)==24 and len(set(ids))==24
assert {i.get('mesh') for i in items}=={a['name'] for inv in inventories for a in inv['assets'] if a['name'].endswith(('_head','_body','_legs'))}
ET.indent(items,space='  ');ET.ElementTree(items).write(module/'ModuleData/items.xml',encoding='utf-8',xml_declaration=True)
assert ET.parse(module/'SubModule.xml').find('Version').get('value')==VERSION
report={'version':VERSION,'status':'pass','check_scope':'offline checks and cumulative module consistency','final_package_sha256':packages[-1]['sha256'],'baseline_version':'v1.2.0','baseline_packages':packages[:3],'packages':packages,'asset_inventory':inventories,'resource_name_and_guid_collisions':False,'previous_three_sets_assets_items_and_source_unchanged':True,'item_count':24,'included_sets':SETS,'editable_sources_verified':True,'all_lod_motion_and_seam_normals_verified':True,'remaining_five_user_acceptance':'pending','eighth_variant':'PVP','game_test_verified':False,'game_cloth_solver_used':False,'cloth_scope':{'existing_sets_preserved':SETS[:4],'cooked_sets':SETS[4:],'independent_cooked_lods':[0,1]},'limitations':'First three sets accepted by user. Final five offline checked only; in-game cloth, IK, body sliders and horse collision await user testing. Sets 5-8 include independently cooked LOD0/LOD1 native-type direct cloth data. Sets 1-4 retain existing cloth setup. Engine dynamics await user testing.'}
(ROOT/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
files=['README.md','mod.json']
if (ROOT/'CHANGELOG.md').is_file():files.append('CHANGELOG.md')
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
config={'id':'ZhenwuCollection','source_files':sorted(set(files)),'package':packages[-1]['file'],'packages':[p['file'] for p in packages],'validation_report':'reports/release_validation.json','included_sets':SETS,'eighth_set_variant':'PVP','shared_source_files':['tools/cloth_compiler/'+n for n in ['__init__.py','cloth_payload.py','ClothPatch.cs','ClothPatch.csproj','cook_cloth.py','NativeClothProbe.cs','NativeClothProbe.csproj','README.md','research_cloth_topology.py','validation.py']]}
(ROOT/'mod.json').write_text(json.dumps(config,indent=2));print('COLLECTION_DELIVERY_READY',VERSION,len(config['source_files']),'source files',len(names),'unique assets')
