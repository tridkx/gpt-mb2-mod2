"""Finalize manifests from completed verification outputs, without installing."""
from pathlib import Path
import json,hashlib
from datetime import date
R=Path(__file__).resolve().parents[1];W=R.parents[1]
for f in ['release_validation','source_validation','preservation_validation','ui_scope_validation']:
    assert json.loads((R/'reports'/(f+'.json')).read_text())['status']=='pass',f
# Authoring bootstrap is intentionally not a rebuild dependency; adapted scripts
# are the authoritative implementation and must remain independently editable.
source_files=['README.md','CHANGELOG.md','mod.json','.gitignore']
for directory in ['input','source','tools','reports']:
    source_files += [p.relative_to(R).as_posix() for p in (R/directory).rglob('*') if p.is_file() and p.suffix not in ['.log','.blend1','.pyc'] and '.fbm' not in str(p) and p.name not in ['.gitkeep','setup_pipeline.py'] and not any(x in p.parts for x in ['obj','bin','__pycache__'])]
shared=[p.relative_to(W).as_posix() for p in (W/'tools/asset_helpers').rglob('*.py') if '__pycache__' not in p.parts]
cfg=dict(id='ModernGirlRace',source_files=sorted(set(source_files)),shared_source_files=sorted(shared),package='module/ModernGirlRace/AssetPackages/modern_girl.tpac',validation_report='reports/release_validation.json')
(R/'mod.json').write_text(json.dumps(cfg,indent=2),encoding='utf8')
report=json.loads((R/'reports/release_validation.json').read_text())
report.update(source_validation='reports/source_validation.json',proportion_uv_validation='reports/preservation_validation.json',ui_scope_validation='reports/ui_scope_validation.json',date=date.today().isoformat(),game_version='v1.4.8',source_input_sha256=hashlib.sha256((R/'input/model.fbx').read_bytes()).hexdigest())
fix_report=R/'reports/ui_creation_fix_validation.json'
if fix_report.exists():
    fix=json.loads(fix_report.read_text())
    if fix['version']==report['version']:
        assert fix['status']=='pass'
        baseline=json.loads((R/'reports/ui_creation_fix_baseline.json').read_text())
        report.update(ui_creation_fix_validation='reports/ui_creation_fix_validation.json',
                      baseline_package_sha256=baseline['module/ModernGirlRace/AssetPackages/modern_girl.tpac'],
                      baseline_reason='UI-only v0.1.1 repair; TPAC unchanged from v0.1.0; current offline release checks rerun.')
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('MANIFEST_READY',len(source_files),'source files')
