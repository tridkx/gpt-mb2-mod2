"""Validate skin resources, inherited actions and the actual troop transform."""
import copy
import json
from pathlib import Path
from lxml import etree as ET

GAME = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')


def canonical(node):
    # Compare XML structure without the local libxml2 C14N crash on skin children.
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(),
            tuple(canonical(child) for child in node if isinstance(child.tag, str)))


def validate_registration(root):
    cfg = json.loads((root / 'tools/model_config.json').read_text())
    module = root / 'module' / cfg['id']
    data = module / 'ModuleData'
    parser = ET.XMLParser(remove_blank_text=True, remove_comments=True)
    def read(path):
        return ET.parse(str(path), parser)
    native = GAME / 'Modules/Native/ModuleData'
    skins = read(data / 'skins.xml').getroot().find(f"race[@id='{cfg['race']}']")
    native_skins = read(native / 'skins.xml').getroot().find("race[@id='human']")
    assert len(skins) == len(native_skins)
    for skin, old in zip(skins, native_skins):
        assert (skin.get('gender'), skin.get('mesh_maturity_type')) == (old.get('gender'), old.get('mesh_maturity_type'))
        assert skin.get('skeleton') == 'human_skeleton'
        assert skin.get('uses_stitching') == 'false'
        assert skin.get('body_meta_mesh') == 'yqs_body'
        for attr in ['hands_mesh', 'face_meta_mesh', 'legs_mesh']:
            assert skin.get(attr) == 'yqs_hidden'
        for tag in ['hair_meshes', 'beard_meshes']:
            assert dict(skin.find(tag).attrib) == dict(old.find(tag).attrib)
            assert len(skin.find(tag)) == 1
            assert canonical(skin.find(tag)[0]) == canonical(old.find(tag)[0])
    actions = read(data / 'action_sets.xml')
    native_actions = read(native / 'action_sets.xml')
    for action in actions.getroot():
        assert action.get('skeleton') == 'human_skeleton'
        assert native_actions.find(f"action_set[@id='{action.get('base_set')}']") is not None
        assert len(action) == 0  # Preserve native inventory/facegen action mapping.
    monsters = read(data / 'monsters.xml')
    mon = monsters.find(f"Monster[@id='{cfg['race']}']")
    old = read(native / 'monsters.xml').find("Monster[@id='human']")
    expected = copy.deepcopy(old)
    expected.set('id', cfg['race'])
    expected.set('action_set', 'as_yqs_warrior')
    expected.set('female_action_set', 'as_yqs_female_warrior')
    assert canonical(mon) == canonical(expected)
    source = read(GAME / 'Modules/SandBoxCore/ModuleData/spnpccharacters.xml')
    result = ET.XSLT(read(data / 'yqs_troops.xslt'))(source)
    before = {n.get('id'): n for n in source.getroot()}
    after = {n.get('id'): n for n in result.getroot()}
    assert before.keys() == after.keys()
    changed = [key for key in before if canonical(before[key]) != canonical(after[key])]
    assert changed == [cfg['target_troop']], changed
    original, troop = before[cfg['target_troop']], after[cfg['target_troop']]
    assert troop.get('race') == cfg['race'] and troop.get('is_female') == 'true'
    for attr in ['level', 'culture', 'occupation']:
        assert troop.get(attr) == original.get(attr)
    for tag in ['skills', 'upgrade_targets']:
        a, b = original.find(tag), troop.find(tag)
        assert (a is None and b is None) or canonical(a) == canonical(b)
    weapons = lambda n: [dict(i.attrib) for roster in n.findall('Equipments/EquipmentRoster') for i in roster if i.get('slot') in ['Item0','Item1','Item2','Item3','Horse','HorseHarness']]
    assert weapons(troop) == weapons(original)
    assert all(i.get('slot') in ['Item0','Item1','Item2','Item3','Horse','HorseHarness'] for roster in troop.findall('Equipments/EquipmentRoster') for i in roster)
    for node in read(data / 'project.mbproj').getroot():
        assert (module / node.get('name')).is_file()
    report = {'status':'pass', 'race':cfg['race'], 'changed_troops':changed,
              'unaffected_troops':len(before)-1, 'native_level_skills_weapons_upgrades_preserved':True,
              'armor_rosters_empty':True, 'skin_variants':len(skins),
              'skeleton':'human_skeleton', 'native_monster_dimensions_preserved':True,
              'native_ui_actions_inherited':True, 'cloth_simulation':False}
    (root / 'reports/registration_validation.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    print(json.dumps(validate_registration(Path(__file__).resolve().parents[1]), indent=2))
