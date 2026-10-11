"""Read-only scale audit of installed races and existing UI runtime logs."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
W=next(p for p in R.parents if (p/'tools/asset_helpers').is_dir())
G=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules')
rows=[]
for relative,ident,sourcefile,heightkey in [
 ('mods/WuduRaceTest','WuduRaceTest','reports/source_validation.json','total_height_m'),
 ('mods/Xianjian7Race/YueQingShuRace','YueQingShuRace','reports/weight_transfer.json','height_m'),
 ('mods/ResidentEvil/REAdaWongRace','REAdaWongRace','reports/geometry_fidelity.json','height_m'),
 ('mods/TianxiangRaceColletion/TianxiangT5PVERace','TianxiangT5PVERace','reports/weight_transfer.json','height_m')]:
 p=W/relative;cfg=json.loads((p/'tools/model_config.json').read_text());height=json.loads((p/sourcefile).read_text()).get(heightkey)
 module=p/'module'/ident
 own=module/'ModuleData/skins.xml';installed=G/ident/'ModuleData/skins.xml'
 skins=[dict(s.attrib) for s in ET.parse(own).findall('race/skin')]
 log=Path.home()/'Documents/Mount and Blade II Bannerlord'/ident/'ui_runtime_v0.1.3.jsonl'
 captures=[]
 if log.is_file():
  records=[json.loads(line) for line in log.read_text(encoding='utf8').splitlines() if line]
  captures=[x for x in records if x['record']['kind'] in ['ada_pose','tianxiang_pose']]
 scales=sorted({x['record']['scale'] for x in captures})
 rows.append({'id':ident,'configured_skin_min_scale':cfg.get('skin_min_scale'),'configured_unit_scale':cfg.get('unit_scale'),'source_height_m':height,
 'adult_skins':[{'gender':s['gender'],'min_scale':float(s['min_scale']),'skeleton':s['skeleton']} for s in skins if s['mesh_maturity_type']=='adult'],
 'installed_skins_match':installed.is_file() and own.read_bytes()==installed.read_bytes(),
 'ui_log':str(log) if captures else None,'ui_capture_count':len(captures),'ui_scales':scales,
 'ui_skeletons':sorted({x['record']['skeleton'] for x in captures}),
 'last_ui_capture':{'time':captures[-1]['time'],'screen':captures[-1]['record']['screen'],'gender':captures[-1]['record']['skeleton_type'],'scale':captures[-1]['record']['scale'],'action_set':captures[-1]['record']['action_set']} if captures else None,
 'rest_height_times_observed_ui_scale_m':[height*s for s in scales] if height else [],
 'height_estimate_scope':'Rest mesh height multiplied by logged scale, not a posed world-space head-to-ground measurement'})
native=[{'gender':s.get('gender'),'min_scale':float(s.get('min_scale'))} for s in ET.parse(G/'Native/ModuleData/skins.xml').findall('race/skin') if s.get('mesh_maturity_type')=='adult']
report={'date':'2026-10-12','scope':'Existing configurations, installed XML, preserved source reports, actual UI captures and local DLL decompilation; no module writes or game launch',
 'races':rows,'native_adult_skins':native,
 'confirmed_findings':['Tianxiang uses its own 1.654 m mesh and measured T5 joint landmarks, not Wudu height data.',
 'Tianxiang and Yue Qingshu registrations use skin_min_scale=1.0; this is a reused default requiring per-race runtime calibration.',
 'Tianxiang actual male character-creation UI scale is 0.9031746 with its own skeleton.',
 'Ada current UI scale is 0.993492067 with min_scale=1.1, approximately 1.1 times the Tianxiang recorded scale.',
 'AgentVisuals.Refresh computes scale through MBBodyProperties.GetScaleFromKey(race,gender,bodyProperties) when ScaleData=0.',
 'GetScaleFromKey delegates to native IMBFaceGen; its exact numeric formula is not present in managed DLLs.',
 'Own UI repair preserves the observed scale; it does not impose a Wudu scale.'],
 'not_proven':['Battle AgentScale has no captured runtime sample for this feedback.',
 'Female, different body keys and ages may yield other scales; male preview data does not calibrate every character.',
 'Yue Qingshu has no captured scale in this audit; similarity of min_scale alone does not prove its runtime value.'],
 'user_feedback':'Both battlefield and character creation/preview appear short.',
 'workflow_gap':'Original model proportions and offline resource dimensions were checked, but in-game effective adult size was not calibrated.'}
(R/'reports/height_diagnosis_2026-10-12.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'races':[{k:x[k] for k in ['id','source_height_m','configured_skin_min_scale','ui_scales','rest_height_times_observed_ui_scale_m','installed_skins_match']} for x in rows]},ensure_ascii=False,indent=2))
