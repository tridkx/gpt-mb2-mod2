"""Preserve source inputs and register an isolated v1.4.8 race probe."""
import copy, json, shutil, hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[1]
WS=R.parents[1]
GAME=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
N=GAME/'Modules/Native/ModuleData'
SC=GAME/'Modules/SandBoxCore/ModuleData'
SOURCE=Path('D:/dsh-tiandao/五毒少女校服8套/01苍蓝流苏')
M=R/'module/WuduRaceTest'
RACE='wdr_canglan'
cfg=json.loads((R/'tools/model_config.json').read_text());K=cfg['unit_scale']/.01
def write(path, root):
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
for p in SOURCE.iterdir():
    if p.is_file(): shutil.copy2(p,R/'input'/p.name)
for p in (SOURCE/'tex').iterdir():
    if p.is_file(): shutil.copy2(p,R/'tex'/p.name)
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['input','tex'] for p in (R/folder).iterdir() if p.is_file() and p.name!='.gitkeep'}
(R/'reports/input_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')

# All ten gender/maturity variants avoid missing-skin lookups in UI code.
# The requested troop is female and adult; other variants are only fallbacks.
skins=ET.Element('skins');race=ET.SubElement(skins,'race',id=RACE,name=RACE)
human=ET.parse(N/'skins.xml').getroot().find("race[@id='human']")
for old in human.findall('skin'):
    skin=copy.deepcopy(old); skin.set('name',RACE+'_'+old.get('name'))
    skin.set('skeleton','wdr_skeleton');skin.set('min_scale',str(cfg['skin_min_scale']))
    skin.set('uses_stitching','false');skin.set('body_mesh_suffix','')
    skin.set('body_meta_mesh','wdr_canglan_body')
    for attr in ['body_meta_mesh_shoulders','body_meta_mesh_upperbody','legs_mesh','hands_mesh','face_meta_mesh','underwear_bottom_mesh','underwear_top_mesh']:
        skin.set(attr,'wdr_hidden')
    skin.set('hands_mesh','wdr_canglan_hands')
    # Native reads hair_meshes/group_id before testing for a missing node.
    # Preserve container attributes and order; remove only variant entries.
    for node in list(skin):
        if node.tag in ['deform_keys','presets','default_hair_meshes','hair_meshes','beard_meshes']:
            for child in list(node):node.remove(child)
            if node.tag in ['hair_meshes','beard_meshes']:
                # Index zero is the native no-hair/no-beard descriptor, not an empty list.
                baseline=old.find(node.tag)[0]
                assert baseline.get('name') is None
                node.append(copy.deepcopy(baseline))
    race.append(skin)
write(M/'ModuleData/skins.xml',skins)

actions=ET.Element('action_sets')
for base,new in [('as_human_warrior','as_wdr_warrior'),('as_human_female_warrior','as_wdr_female_warrior'),('as_human_villager','as_wdr_villager')]:
    node=ET.SubElement(actions,'action_set',id=new,skeleton='wdr_skeleton',movement_system='bipedal',base_set=base)
write(M/'ModuleData/action_sets.xml',actions)
monsters=ET.Element('Monsters')
native_monsters=ET.parse(N/'monsters.xml').getroot()
monster=copy.deepcopy(native_monsters.find("Monster[@id='human']"))
monster.set('id',RACE);monster.set('action_set','as_wdr_warrior');monster.set('female_action_set','as_wdr_female_warrior')
# Basic camera/capsule sizes; detailed combat collision fitting is out of scope.
for k,v in {'standing_chest_height':'1.00','standing_pelvis_height':'.75','standing_eye_height':'1.23','crouch_eye_height':'.80','mounted_eye_height':'.55','arm_length':'.55'}.items():monster.set(k,str(float(v)*K))
for capsule in monster.findall('Capsules/*'):
    capsule.set('radius',str(.16*K));capsule.set('pos1',f'0.0, 0.0, {1.15*K}');capsule.set('pos2',f'0.0, 0.0, {.35*K}')
monsters.append(monster)
for suffix in ['_settlement','_settlement_slow','_settlement_fast','_child']:
    ET.SubElement(monsters,'Monster',id=RACE+suffix,base_monster=RACE,action_set='as_wdr_villager',female_action_set='as_wdr_villager')
write(M/'ModuleData/monsters.xml',monsters)

troop=copy.deepcopy(ET.parse(SC/'spnpccharacters.xml').getroot().find("NPCCharacter[@id='imperial_recruit']"))
troop.set('race',RACE);troop.set('is_female','true');troop.set('age','25');troop.set('face_mesh_cache','false')
troop.set('name','五毒苍蓝新兵')
troop.find('face').clear()
ET.SubElement(troop.find('face'),'BodyProperties',version='4',age='25',weight='0.5',build='0.5',key='0'*128)
ET.SubElement(troop.find('face'),'BodyPropertiesMax',version='4',age='25',weight='0.5',build='0.5',key='0'*128)
equipment=troop.find('Equipments')
for node in list(equipment):
    if node.tag=='EquipmentRoster':
        for item in list(node):
            if item.get('slot') not in ['Item0','Item1','Item2','Item3']:node.remove(item)
    else:equipment.remove(node)
ET.SubElement(equipment,'EquipmentRoster',equipmentType='Civilian')
troops=ET.Element('NPCCharacters');troops.append(troop)
write(M/'ModuleData/wdr_troops.xml',troops)
# XSLT replaces the entire target node so native armor rosters cannot merge back.
X='http://www.w3.org/1999/XSL/Transform';ET.register_namespace('xsl',X)
xs=ET.Element('{'+X+'}stylesheet',version='1.0')
ET.SubElement(xs,'{'+X+'}output',method='xml',encoding='utf-8',indent='yes')
identity=ET.SubElement(xs,'{'+X+'}template',match='@*|node()')
cp=ET.SubElement(identity,'{'+X+'}copy');ET.SubElement(cp,'{'+X+'}apply-templates',select='@*|node()')
replace=ET.SubElement(xs,'{'+X+'}template',match="NPCCharacter[@id='imperial_recruit']")
replace.append(copy.deepcopy(troop));write(M/'ModuleData/wdr_troops.xslt',xs)

project=ET.Element('base',type='solution')
for id,filename,type in [('soln_skins','skins.xml','skin'),('soln_action_sets','action_sets.xml','action_set'),('soln_monsters','monsters.xml','monster')]:
    ET.SubElement(project,'file',id=id,name='ModuleData/'+filename,type=type)
write(M/'ModuleData/project.mbproj',project)
sub=ET.Element('Module')
for name,value in [('Name','Wudu Canglan Race Test'),('Id','WuduRaceTest'),('Version',cfg['version']),('DefaultModule','false'),('ModuleCategory','Singleplayer'),('ModuleType','Community'),('SingleplayerModule','true'),('MultiplayerModule','false')]:ET.SubElement(sub,name,value=value)
deps=ET.SubElement(sub,'DependedModules')
for dep in ['Native','SandBoxCore','Sandbox']:ET.SubElement(deps,'DependedModule',Id=dep)
submodules=ET.SubElement(sub,'SubModules');observer=ET.SubElement(submodules,'SubModule')
for tag,value in [('Name','Wudu Race Observer'),('DLLName','WuduRaceTest.dll'),('SubModuleClassType','WuduRaceTest.SubModule')]:ET.SubElement(observer,tag,value=value)
tags=ET.SubElement(observer,'Tags');ET.SubElement(tags,'Tag',key='DedicatedServerType',value='none');ET.SubElement(tags,'Tag',key='IsNoRenderModeElement',value='false')
xmls=ET.SubElement(sub,'Xmls')
for id,path in [('Monsters','monsters'),('NPCCharacters','wdr_troops')]:
    x=ET.SubElement(xmls,'XmlNode');ET.SubElement(x,'XmlName',id=id,path=path)
    types=ET.SubElement(x,'IncludedGameTypes')
    for type in ['Campaign','CampaignStoryMode','CustomGame']:ET.SubElement(types,'GameType',value=type)
write(M/'SubModule.xml',sub)
print('INPUTS_AND_MODULE_READY')
