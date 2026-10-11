"""Register the fixed Ada body and replace only the imperial recruit."""
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
NATIVE = GAME / 'Modules/Native/ModuleData'
CORE = GAME / 'Modules/SandBoxCore/ModuleData'
CFG = json.loads((ROOT / 'tools/model_config.json').read_text())
assert ET.parse(GAME / 'Modules/Native/SubModule.xml').getroot().find('Version').get('value') == 'v1.4.8', 'Recheck registration against the current Native version'
MODULE = ROOT / 'module' / CFG['id']
RACE = CFG['race']


def write(path, root):
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


skins = ET.Element('skins')
race = ET.SubElement(skins, 'race', id=RACE)
human = ET.parse(NATIVE / 'skins.xml').getroot().find("race[@id='human']")
for old in human.findall('skin'):
    skin = copy.deepcopy(old)
    skin.set('name', RACE + '_' + old.get('name'))
    skin.set('skeleton', CFG['skeleton'])
    skin.set('min_scale', str(CFG['skin_min_scale']))
    skin.set('uses_stitching', 'false')
    skin.set('body_mesh_suffix', '')
    skin.set('body_meta_mesh', 'adar_body')
    for attr in ['body_meta_mesh_shoulders', 'body_meta_mesh_upperbody', 'legs_mesh',
                 'hands_mesh', 'face_meta_mesh', 'underwear_bottom_mesh', 'underwear_top_mesh']:
        skin.set(attr, 'adar_hidden')
    for node in skin:
        if node.tag in ['deform_keys', 'presets', 'default_hair_meshes', 'hair_meshes', 'beard_meshes']:
            for child in list(node):
                node.remove(child)
            if node.tag in ['hair_meshes', 'beard_meshes']:
                baseline = old.find(node.tag)[0]
                assert baseline.get('name') is None
                node.append(copy.deepcopy(baseline))
    race.append(skin)
write(MODULE / 'ModuleData/skins.xml', skins)

# Use the Ada bind skeleton with inherited native UI actions.
actions = ET.Element('action_sets')
for suffix, base in [('warrior', 'as_human_warrior'), ('female_warrior', 'as_human_female_warrior'),
                     ('villager', 'as_human_villager'), ('female_villager', 'as_human_female_villager'),
                     ('facegen', 'as_human_facegen'), ('female_facegen', 'as_human_female_facegen')]:
    ET.SubElement(actions, 'action_set', id='as_reada_wong_' + suffix,
                  skeleton=CFG['skeleton'], movement_system='bipedal', base_set=base)
write(MODULE / 'ModuleData/action_sets.xml', actions)

monsters = ET.Element('Monsters')
native_monster = ET.parse(NATIVE / 'monsters.xml').getroot().find("Monster[@id='human']")
monster = copy.deepcopy(native_monster)
monster.set('id', RACE)
monster.set('action_set', 'as_reada_wong_warrior')
monster.set('female_action_set', 'as_reada_wong_female_warrior')
monsters.append(monster)
for suffix in ['_settlement', '_settlement_slow', '_settlement_fast', '_child']:
    ET.SubElement(monsters, 'Monster', id=RACE + suffix, base_monster=RACE,
                  action_set='as_reada_wong_villager', female_action_set='as_reada_wong_female_villager')
write(MODULE / 'ModuleData/monsters.xml', monsters)

target = CFG['target_troop']
troop = copy.deepcopy(ET.parse(CORE / 'spnpccharacters.xml').getroot().find(f"NPCCharacter[@id='{target}']"))
troop.set('race', RACE)
troop.set('is_female', 'true')
troop.set('age', '25')
troop.set('face_mesh_cache', 'false')
troop.set('name', '艾达王新兵')
face = troop.find('face')
face.clear()
for tag in ['BodyProperties', 'BodyPropertiesMax']:
    ET.SubElement(face, tag, version='4', age='25', weight='0.5', build='0.5', key='0' * 128)
equipment = troop.find('Equipments')
for node in list(equipment):
    if node.tag == 'EquipmentRoster':
        for item in list(node):
            if item.get('slot') not in ['Item0', 'Item1', 'Item2', 'Item3', 'Horse', 'HorseHarness']:
                node.remove(item)
    else:
        equipment.remove(node)
ET.SubElement(equipment, 'EquipmentRoster', equipmentType='Civilian')
troops = ET.Element('NPCCharacters')
troops.append(troop)
write(MODULE / 'ModuleData/adar_troops.xml', troops)

# Replace the whole node to prevent armor being merged back into the body.
X = 'http://www.w3.org/1999/XSL/Transform'
ET.register_namespace('xsl', X)
xs = ET.Element('{' + X + '}stylesheet', version='1.0')
ET.SubElement(xs, '{' + X + '}output', method='xml', encoding='utf-8', indent='yes')
identity = ET.SubElement(xs, '{' + X + '}template', match='@*|node()')
cp = ET.SubElement(identity, '{' + X + '}copy')
ET.SubElement(cp, '{' + X + '}apply-templates', select='@*|node()')
replace = ET.SubElement(xs, '{' + X + '}template', match=f"NPCCharacter[@id='{target}']")
replace.append(copy.deepcopy(troop))
write(MODULE / 'ModuleData/adar_troops.xslt', xs)

project = ET.Element('base', type='solution')
for ident, filename, kind in [('soln_skins', 'skins.xml', 'skin'),
                              ('soln_action_sets', 'action_sets.xml', 'action_set'),
                              ('soln_monsters', 'monsters.xml', 'monster')]:
    ET.SubElement(project, 'file', id=ident, name='ModuleData/' + filename, type=kind)
write(MODULE / 'ModuleData/project.mbproj', project)

sub = ET.Element('Module')
for tag, value in [('Name', 'Resident Evil - Ada Wong Race'), ('Id', CFG['id']),
                   ('Version', CFG['version']), ('DefaultModule', 'false'),
                   ('ModuleCategory', 'Singleplayer'), ('ModuleType', 'Community'),
                   ('SingleplayerModule', 'true'), ('MultiplayerModule', 'false')]:
    ET.SubElement(sub, tag, value=value)
deps = ET.SubElement(sub, 'DependedModules')
for dep in ['Native', 'SandBoxCore', 'Sandbox']:
    ET.SubElement(deps, 'DependedModule', Id=dep)
submodules = ET.SubElement(sub, 'SubModules')
if CFG.get('ui_preview_repair'):
    runtime = ET.SubElement(submodules, 'SubModule')
    ET.SubElement(runtime, 'Name', value='Ada UI Preview Skeleton Repair')
    ET.SubElement(runtime, 'DLLName', value='REAdaWongRace.UIRuntime.dll')
    ET.SubElement(runtime, 'SubModuleClassType', value='REAdaWongRace.UIProbe.SubModule')
    ET.SubElement(runtime, 'Tags')
xmls = ET.SubElement(sub, 'Xmls')
for ident, path in [('Monsters', 'monsters'), ('NPCCharacters', 'adar_troops')]:
    node = ET.SubElement(xmls, 'XmlNode')
    ET.SubElement(node, 'XmlName', id=ident, path=path)
    types = ET.SubElement(node, 'IncludedGameTypes')
    for kind in ['Campaign', 'CampaignStoryMode', 'CustomGame']:
        ET.SubElement(types, 'GameType', value=kind)
write(MODULE / 'SubModule.xml', sub)
print('ADA_RACE_REGISTERED', RACE, target)
