"""Finalize manifests from completed verification outputs, without installing."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];W=R.parents[1]
for f in ['release_validation','source_validation','preservation_validation','ui_scope_validation']:
    assert json.loads((R/'reports'/(f+'.json')).read_text())['status']=='pass',f
# Authoring bootstrap is intentionally not a rebuild dependency; adapted scripts
# are the authoritative implementation and must remain independently editable.
source_files=['README.md','CHANGELOG.md','mod.json','.gitignore','.gitattributes']
for directory in ['input','source','tools','reports']:
    source_files += [p.relative_to(R).as_posix() for p in (R/directory).rglob('*') if p.is_file() and p.suffix not in ['.log','.blend1','.pyc'] and '.fbm' not in str(p) and p.name not in ['.gitkeep','setup_pipeline.py'] and not any(x in p.parts for x in ['obj','bin','__pycache__'])]
shared=[p.relative_to(W).as_posix() for p in (W/'tools/asset_helpers').rglob('*.py') if '__pycache__' not in p.parts]
cfg=dict(id='BoRuRace',source_files=sorted(set(source_files)),shared_source_files=sorted(shared),package='module/BoRuRace/AssetPackages/boru_race.tpac',validation_report='reports/release_validation.json')
(R/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf8')
report=json.loads((R/'reports/release_validation.json').read_text())
report.update(source_validation='reports/source_validation.json',proportion_uv_validation='reports/preservation_validation.json',ui_scope_validation='reports/ui_scope_validation.json',date='2026-10-13',game_version='v1.4.8',source_input_sha256=hashlib.sha256((R/'input/SK_BR_nofoot.psk').read_bytes()).hexdigest(),ui_scope=json.loads((R/'tools/model_config.json').read_text())['ui_scope'])
report['limitations'][0]='Fixed appearance; hair and clothes use skeletal skinning without physics. Source diffuse/normal and body ORM retained; unavailable cloth controls and untextured accessory parameters use documented conservative fallbacks.'
acceptance=R/'reports/user_acceptance.json'
if acceptance.is_file():
    confirmed=json.loads(acceptance.read_text(encoding='utf8'))
    if confirmed['version']==report['version'] and confirmed['package_sha256']==report['final_package_sha256']:
        report.update(game_test_verified=True,game_test_scope=confirmed['scope'],game_test_evidence='user confirmation',user_acceptance='reports/user_acceptance.json')
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('MANIFEST_READY',len(source_files),'source files')
