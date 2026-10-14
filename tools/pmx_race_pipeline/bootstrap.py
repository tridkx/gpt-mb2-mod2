"""Preserve archives and unpack into independent character projects safely."""
import json,zipfile,shutil,secrets,hashlib
from pathlib import Path
from inventory import inventory,entry_name
W=Path(__file__).resolve().parents[2];SERIES=W/'mods/GenshinRaceCollection';SOURCE=Path('C:/Users/DKX/Desktop/新建文件夹 (3)/原神')
PLAN=[
 ('ganyu_','GanyuRace','ganyu','Ganyu Race','甘雨','甘雨.pmx'),
 ('「叶隐芳名」','LisaLeafShadeRace','lisa_leafshade','Lisa Leaf Shade Race','丽莎·叶隐芳名','丽莎.pmx'),
 ('「花时来信」','AyakaSpringBloomRace','ayaka_springbloom','Ayaka Spring Bloom Race','神里绫华·花时来信','神里绫华.pmx'),
 ('【女主角','LumineRace','lumine','Lumine Race','荧','荧.pmx'),
 ('【模之屋】「纱中幽兰」','NingguangOrchidRace','ningguang_orchid','Ningguang Orchid Race','凝光·纱中幽兰','凝光.pmx'),
 ('【模之屋】云堇','YunJinRace','yunjin','Yun Jin Race','云堇','云堇.pmx'),
 ('【模之屋】砂糖','SucroseRace','sucrose','Sucrose Race','砂糖','砂糖.pmx'),
 ('【珊瑚宫心海','KokomiRace','kokomi','Kokomi Race','珊瑚宫心海','珊瑚宫心海.pmx'),
 ('【芙宁娜','FurinaRace','furina','Furina Race','芙宁娜',None),
 ('【闲云','XianyunRace','xianyun','Xianyun Race','闲云','闲云.pmx'),
 ('丽莎_by','LisaRace','lisa','Lisa Race','丽莎','丽莎/丽莎.pmx'),
 ('妮露_by','NilouRace','nilou','Nilou Race','妮露','妮露.pmx'),
 ('安柏_by','AmberRace','amber','Amber Race','安柏','安柏/安柏.pmx'),
 ('模之屋-【刻晴','KeqingOpulentRace','keqing_opulent','Keqing Opulent Race','刻晴·霓裾翩跹','刻晴.pmx'),
 ('模之屋【八重神子','YaeMikoRace','yaemiko','Yae Miko Race','八重神子','八重神子.pmx'),
 ('琴时装','JeanSeaBreezeRace','jean_seabreeze','Jean Sea Breeze Race','琴·时装','琴.pmx'),
 ('神里绫华-模','AyakaRace','ayaka','Ayaka Race','神里绫华','神里绫华.pmx'),
 ('胡桃-海灯节','HuTaoLanternRace','hutao_lantern','Hu Tao Lantern Race','胡桃·海灯节','胡桃-海灯节.pmx'),
 ('胡桃_by','HuTaoRace','hutao','Hu Tao Race','胡桃','胡桃.pmx'),
 ('薇斯纳_by','WeisinaRace','weisina','Weisina Race','薇斯纳','薇斯纳.pmx'),
 ('诺艾尔_by','NoelleRace','noelle','Noelle Race','诺艾尔','诺艾尔.pmx')]

def main():
    records=inventory(SOURCE);result=[]
    for prefix,ident,race,english,chinese,model in PLAN:
        rows=[r for r in records if r['archive'].startswith(prefix)];assert len(rows)==1,prefix
        row=rows[0];root=SERIES/ident
        for sub in ['input/original','input/archive','source','tex','tools','build','reports','dist',f'module/{ident}/ModuleData',f'module/{ident}/AssetPackages']:(root/sub).mkdir(parents=True,exist_ok=True)
        archive=SOURCE/row['archive'];saved=root/'input/archive'/archive.name
        if not saved.exists():shutil.copy2(archive,saved)
        assert hashlib.sha256(saved.read_bytes()).digest()==hashlib.sha256(archive.read_bytes()).digest()
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                name=entry_name(info);path=(root/'input/original'/name).resolve()
                assert path.is_relative_to((root/'input/original').resolve()),name
                if info.is_dir():path.mkdir(parents=True,exist_ok=True);continue
                path.parent.mkdir(parents=True,exist_ok=True)
                data=z.read(info)
                if path.exists():assert path.read_bytes()==data,path
                else:path.write_bytes(data)
        cfg_path=root/'tools/model_config.json'
        if cfg_path.exists():cfg=json.loads(cfg_path.read_text(encoding='utf8'));model=cfg['source_model'].split('input/original/',1)[1]
        else:
            if model is None:model=secrets.choice(row['models'])
            cfg={'id':ident,'version':'v0.1.0','race':race,'prefix':race,'module_name':english,'display_name':chinese,'source_model':'input/original/'+model,'source_archive':'input/archive/'+row['archive'],'ignored_models':[p for p in row['models'] if p!=model],'unit_scale':.08,'source_rotation':[[-1,0,0],[0,0,-1],[0,1,0]],'skin_min_scale':1.0,'cloth_enabled':False,'cloth_lods':[],'cloth_parts':{},'lod_multipliers':[1,.65,.4,.2],'minimum_ratios':{},'facial_animation':False,'pmx_reader':'C:/Users/DKX/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/user_default/mmd_tools/core/pmx/__init__.py'}
            cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
        cfg.setdefault('skeleton',race+'_skeleton')
        if ident=='XianyunRace':cfg['overlay_materials']=['髮s']
        if ident=='WeisinaRace':cfg['overlay_materials']=['袜s','袜s2']
        cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
        assert (root/cfg['source_model']).is_file()
        for name in ['.gitattributes','.gitignore']:
            src=SERIES/'EmilieRace'/name;dest=root/name
            if not dest.exists():shutil.copy2(src,dest)
        result.append({'id':ident,'race':race,'name':chinese,'root':str(root),'source':cfg['source_model'],'ignored_models':cfg['ignored_models'],'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()})
    (SERIES/'batch_inventory.json').write_text(json.dumps({'date':'2026-10-14','source_directory':str(SOURCE),'skipped':['EmilieRace'],'characters':result},ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
