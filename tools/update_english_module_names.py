"""Apply the user's launcher display-name preference; preserve IDs and versions."""
from pathlib import Path
import re, json, hashlib, zipfile, shutil, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
SKILL=Path('C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/SKILL.md')
rule='- 本用户要求：SubModule.xml 的 Module/Name（模组管理器显示名）必须用英文，避免中文显示为问号；游戏内装备名称可用中文。只改显示名时保留模组 ID、目录、资源名和版本，同步工程、已安装模块与当前交付包，并保留原交付包。'
skill=SKILL.read_text(encoding='utf-8')
if rule not in skill:
    anchor='## 新模型制作'
    assert anchor in skill
    SKILL.write_text(skill.replace(anchor,rule+'\n\n'+anchor),encoding='utf-8')
changes=[]
def renamed(data,name):
    root=ET.fromstring(data);old=root.find('Name').get('value')
    result,count=re.subn(rb'(<Name\s+value=")[^"]*("\s*/>)',lambda m:m[1]+name.encode()+m[2],data,count=1)
    assert count==1
    updated=ET.fromstring(result)
    assert root.find('Id').attrib==updated.find('Id').attrib
    assert root.find('Version').attrib==updated.find('Version').attrib
    return result,old
for mod,name in [('TianxiangT5','Tianxiang T5'),('HanfuBlueRed','Hanfu Blue Red')]:
    project=ROOT/'mods'/mod;path=project/'module'/mod/'SubModule.xml'
    data,old=renamed(path.read_bytes(),name);path.write_bytes(data)
    installed=GAME/'Modules'/mod/'SubModule.xml'
    if installed.exists():
        content,installed_old=renamed(installed.read_bytes(),name);installed.write_bytes(content)
    version=ET.fromstring(data).find('Version').get('value')
    archives=[]
    for kind in ['Mod','Source']:
        archive=project/'dist'/f'{mod}_{kind}.zip'
        if not archive.exists():continue
        entry=f'{mod}/SubModule.xml' if kind=='Mod' else f'module/{mod}/SubModule.xml'
        with zipfile.ZipFile(archive) as z:
            if entry not in z.namelist():continue
            source=z.read(entry)
            if ET.fromstring(source).find('Version').get('value')!=version:continue
            new,_=renamed(source,name)
            if new==source:continue
            members=[(i,z.read(i.filename)) for i in z.infolist()]
        backup=archive.with_name(archive.stem+'_before_english_name_20261008.zip')
        if not backup.exists():shutil.copy2(archive,backup)
        tmp=archive.with_suffix('.zip.tmp')
        with zipfile.ZipFile(tmp,'w') as z:
            for info,content in members:z.writestr(info,new if info.filename==entry else content)
        with zipfile.ZipFile(tmp) as z:
            assert z.testzip() is None
            for info,content in members:assert z.read(info.filename)==(new if info.filename==entry else content)
        tmp.replace(archive);archives.append(str(archive))
    changes.append({'id':mod,'old_name':old,'name':name,'version':version,'installed_synced':installed.exists(),'archives':archives})
print(json.dumps({'skill_updated':rule in SKILL.read_text(encoding='utf-8'),'modules':changes},ensure_ascii=False,indent=2))
