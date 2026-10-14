"""Resolve preview actions through Native clip GUIDs, not similar names."""
import json,re,subprocess,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
native={a.get('id'):a for a in E.parse(N/'ModuleData/action_sets.xml').getroot()}
def inherited(name):
    node=native[name];result=inherited(node.get('base_set')) if node.get('base_set') else {}
    result.update({a.get('type'):a.get('animation') for a in node});return result
own={a.get('id'):a for a in E.parse(R/'module/YueQingShuRace/ModuleData/action_sets.xml').getroot()};rows=[]
for sex,prefix,label in [('male','','ui_neutral_male'),('female','female_','ui_neutral_female')]:
    actions={a.get('type'):a.get('animation') for a in own['as_yqs_'+prefix+'warrior']}
    original=inherited('as_human_female_facegen')
    for action,clip in actions.items():
        assert original[action]==clip
        output=subprocess.check_output(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','clip',str(N/'AssetPackages/animation_clips.tpac'),clip],text=True,encoding='utf8')
        guid=re.search(r'duration=.* animation=([^\s]+)',output).group(1)
        raw=json.loads((R/'reports'/(label+'.json')).read_text())
        assert raw['guid']==guid,(raw.keys(),guid)
        if action=='act_inventory_idle':assert 'cyclic' in output
        rows.append({'sex':sex,'action':action,'clip':clip,'skeletal_animation':raw['name'],'skeletal_animation_guid':guid,'clip_metadata':output})
    assert len(own['as_yqs_'+prefix+'facegen'])==0
import zipfile
def semantic(node):
    # XML indentation/tails can change when scene registrations are appended.
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(),
            tuple(semantic(child) for child in node))
baseline_archive=R/'dist/YueQingShuRace_v0.3.0_Mod.zip'
if not baseline_archive.exists():baseline_archive=R/'dist/YueQingShuRace_Mod.zip'
with zipfile.ZipFile(baseline_archive) as archive:
 old=E.fromstring(archive.read('YueQingShuRace/ModuleData/action_sets.xml'))
 for previous in old:
  current=own[previous.get('id')]
  assert previous.attrib==current.attrib
  if previous.get('id') not in ['as_yqs_warrior','as_yqs_female_warrior']:assert semantic(previous)==semantic(current)
report={'status':'pass','version':json.loads((R/'tools/model_config.json').read_text())['version'],
        'default_inventory_clip':'inventory_idle','preview_overrides':rows,'creation_page_action_mapping_unchanged':True,
        'runtime_dll_unchanged':False,'runtime_scope':'inventory screen only','runtime_entry':'direct CharacterTableauTextureProvider before bounded screen reflection','runtime_effect_verified':False,'selected_character_sex_preserved':True,'fixed_character_preview_pose':'female_idle_long_for_both_preview_skeleton_types','game_retest_pending':True}
(R/'reports/preview_idle_validation.json').write_text(json.dumps(report,indent=2));print('PREVIEW_IDLE_CLIPS_VERIFIED')
