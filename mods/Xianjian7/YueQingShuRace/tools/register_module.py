"""Register the fixed source-proportioned race without troop overrides."""
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
NATIVE = GAME / 'Modules/Native/ModuleData'
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
    skin.set('body_meta_mesh', 'yqs_body')
    for attr in ['body_meta_mesh_shoulders', 'body_meta_mesh_upperbody', 'legs_mesh',
                 'hands_mesh', 'face_meta_mesh', 'underwear_bottom_mesh', 'underwear_top_mesh']:
        skin.set(attr, 'yqs_hidden')
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

# Use source-sized custom bind joints and inherit native actions.
actions = ET.Element('action_sets')
for suffix, base in [('warrior', 'as_human_warrior'), ('female_warrior', 'as_human_female_warrior'),
                     ('villager', 'as_human_villager'), ('female_villager', 'as_human_female_villager'),
                     ('facegen', 'as_human_facegen'), ('female_facegen', 'as_human_female_facegen')]:
    ET.SubElement(actions, 'action_set', id='as_yqs_' + suffix,
                  skeleton=CFG['skeleton'], movement_system='bipedal', base_set=base)
write(MODULE / 'ModuleData/action_sets.xml', actions)

monsters = ET.Element('Monsters')
native_monster = ET.parse(NATIVE / 'monsters.xml').getroot().find("Monster[@id='human']")
monster = copy.deepcopy(native_monster)
monster.set('id', RACE)
monster.set('action_set', 'as_yqs_warrior')
monster.set('female_action_set', 'as_yqs_female_warrior')
monsters.append(monster)
for suffix in ['_settlement', '_settlement_slow', '_settlement_fast', '_child']:
    ET.SubElement(monsters, 'Monster', id=RACE + suffix, base_monster=RACE,
                  action_set='as_yqs_villager', female_action_set='as_yqs_female_villager')
write(MODULE / 'ModuleData/monsters.xml', monsters)

project = ET.Element('base', type='solution')
for ident, filename, kind in [('soln_skins', 'skins.xml', 'skin'),
                              ('soln_action_sets', 'action_sets.xml', 'action_set'),
                              ('soln_monsters', 'monsters.xml', 'monster')]:
    ET.SubElement(project, 'file', id=ident, name='ModuleData/' + filename, type=kind)
write(MODULE / 'ModuleData/project.mbproj', project)

sub = ET.Element('Module')
for tag, value in [('Name', 'Yue Qingshu Race'), ('Id', CFG['id']),
                   ('Version', CFG['version']), ('DefaultModule', 'false'),
                   ('ModuleCategory', 'Singleplayer'), ('ModuleType', 'Community'),
                   ('SingleplayerModule', 'true'), ('MultiplayerModule', 'false')]:
    ET.SubElement(sub, tag, value=value)
deps = ET.SubElement(sub, 'DependedModules')
for dep in ['Native', 'SandBoxCore', 'Sandbox']:
    ET.SubElement(deps, 'DependedModule', Id=dep)
ET.SubElement(sub, 'SubModules')
xmls = ET.SubElement(sub, 'Xmls')
for ident, path in [('Monsters', 'monsters')]:
    node = ET.SubElement(xmls, 'XmlNode')
    ET.SubElement(node, 'XmlName', id=ident, path=path)
    types = ET.SubElement(node, 'IncludedGameTypes')
    for kind in ['Campaign', 'CampaignStoryMode', 'CustomGame']:
        ET.SubElement(types, 'GameType', value=kind)
write(MODULE / 'SubModule.xml', sub)
print('YQS_RACE_REGISTERED', RACE, 'race resources only')
