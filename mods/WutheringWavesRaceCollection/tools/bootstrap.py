"""Preserve the eight supplied archives and inspect each independent PMX."""
from pathlib import Path
import sys,json,zipfile,shutil,hashlib
S=Path(__file__).resolve().parents[1]; W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(W/'tools/pmx_race_pipeline'))
from inventory import inventory,entry_name
from source_inventory import inspect
SOURCE=Path('C:/Users/DKX/Desktop/新建文件夹 (3)/鸣潮')
PLAN=[('今汐1.04','JinhsiRace','jinhsi','Jinhsi Race','今汐'),('今汐皮肤','JinhsiOutfitRace','jinhsi_outfit','Jinhsi Outfit Race','今汐·桃夭灼灼'),('鸣潮_白芷','BaizhiRace','baizhi','Baizhi Race','白芷'),('鸣潮_鉴心','JianxinRace','jianxin','Jianxin Race','鉴心'),('鸣潮_吟霖','YinlinRace','yinlin','Yinlin Race','吟霖'),('守岸人','ShorekeeperRace','shorekeeper','Shorekeeper Race','守岸人'),('长离','ChangliRace','changli','Changli Race','长离'),('折枝','ZhezhiRace','zhezhi','Zhezhi Race','折枝')]
def main():
 rows=inventory(SOURCE);out=[]
 for match,ident,race,english,name in PLAN:
  row=next(r for r in rows if r['archive'].startswith(match));assert len(row['models'])==1,row
  root=S/ident
  for d in ['input/archive','input/original','source','tex','tools','build','reports','dist',f'module/{ident}/ModuleData',f'module/{ident}/AssetPackages']:(root/d).mkdir(parents=True,exist_ok=True)
  archive=SOURCE/row['archive'];saved=root/'input/archive'/archive.name
  if not saved.exists():shutil.copy2(archive,saved)
  assert saved.read_bytes()==archive.read_bytes()
  with zipfile.ZipFile(saved) as z:
   for info in z.infolist():
    p=(root/'input/original'/entry_name(info)).resolve();assert p.is_relative_to((root/'input/original').resolve())
    if info.is_dir():p.mkdir(parents=True,exist_ok=True);continue
    p.parent.mkdir(parents=True,exist_ok=True);data=z.read(info)
    if p.exists():assert p.read_bytes()==data
    else:p.write_bytes(data)
  c={'id':ident,'version':'v0.1.0','race':race,'prefix':'ww_'+race,'skeleton':'ww_'+race+'_skeleton','module_name':english,'display_name':name,'source_model':'input/original/'+row['models'][0],'source_archive':'input/archive/'+row['archive'],'ignored_models':[],'unit_scale':.08,'source_rotation':[[-1,0,0],[0,0,-1],[0,1,0]],'skin_min_scale':1.0,'cloth_enabled':False,'cloth_lods':[],'cloth_parts':{},'cloth_materials':[],'lod_multipliers':[1,.65,.4,.2],'minimum_ratios':{},'facial_animation':False,'pmx_reader':'C:/Users/DKX/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/user_default/mmd_tools/core/pmx/__init__.py'}
  path=root/'tools/model_config.json'
  c['race']=c['prefix']
  if not path.exists():path.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
  for n in ['.gitattributes','.gitignore']:
   dest=root/n
   if not dest.exists():shutil.copy2(W/'mods/GenshinRaceCollection/EmilieRace'/n,dest)
  r=inspect(root)
  out.append({'id':ident,'name':name,'root':str(root),'archive_sha256':hashlib.sha256(saved.read_bytes()).hexdigest()})
  print(ident,'height',round(r['height_source_units'],3),'materials',[(m['index'],m['name'],m['alpha']) for m in r['materials']],'missing textures',[t['path'] for t in r['textures'] if not t['exists']],flush=True)
 (S/'batch_inventory.json').write_text(json.dumps({'date':'2026-10-15','characters':out},ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
