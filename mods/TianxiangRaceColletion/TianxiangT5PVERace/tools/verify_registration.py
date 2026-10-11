"""Validate race resources, inherited actions and absence of troop overrides."""
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
        assert skin.get('skeleton') == cfg['skeleton']
        assert float(skin.get('min_scale')) == cfg['skin_min_scale']
        assert skin.get('uses_stitching') == 'false'
        assert skin.get('body_meta_mesh') == 'txt5pve_body'
        for attr in ['hands_mesh', 'face_meta_mesh', 'legs_mesh']:
            assert skin.get(attr) == 'txt5pve_hidden'
        for tag in ['hair_meshes', 'beard_meshes']:
            assert dict(skin.find(tag).attrib) == dict(old.find(tag).attrib)
            assert len(skin.find(tag)) == 1
            assert canonical(skin.find(tag)[0]) == canonical(old.find(tag)[0])
    actions = read(data / 'action_sets.xml')
    native_actions = read(native / 'action_sets.xml')
    for action in actions.getroot():
        assert action.get('skeleton') == cfg['skeleton']
        assert native_actions.find(f"action_set[@id='{action.get('base_set')}']") is not None
        assert len(action) == 0  # Preserve native inventory/facegen action mapping.
    monsters = read(data / 'monsters.xml')
    mon = monsters.find(f"Monster[@id='{cfg['race']}']")
    old = read(native / 'monsters.xml').find("Monster[@id='human']")
    expected = copy.deepcopy(old)
    expected.set('id', cfg['race'])
    expected.set('action_set', 'as_txt5pve_warrior')
    expected.set('female_action_set', 'as_txt5pve_female_warrior')
    assert canonical(mon) == canonical(expected)
    descriptor=read(module / 'SubModule.xml')
    assert [node.get('id') for node in descriptor.findall('Xmls/XmlNode/XmlName')]==['Monsters']
    assert not list(data.glob('*troop*'))
    native_troop_count=len(read(GAME / 'Modules/SandBoxCore/ModuleData/spnpccharacters.xml').getroot())
    for node in read(data / 'project.mbproj').getroot():
        assert (module / node.get('name')).is_file()
    report = {'status':'pass', 'race':cfg['race'], 'changed_troops':[],
              'unaffected_troops':native_troop_count, 'troop_overrides_present':False,
              'skin_variants':len(skins), 'skeleton':cfg['skeleton'],
              'native_monster_dimensions_preserved':True,
              'native_ui_actions_inherited':True, 'cloth_simulation':cfg['cloth_enabled']}
    (root / 'reports/registration_validation.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    print(json.dumps(validate_registration(Path(__file__).resolve().parents[1]), indent=2))
