"""Attest the scoped inventory runtime repair against published v0.1.5."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
W=next(p for p in R.parents if (p/'.git').exists())
PREVIOUS='v0.1.5'
TAG='TianxiangGirlT1Race/'+PREVIOUS
def old(p):
    return subprocess.check_output(['git','show',TAG+':'+p.relative_to(W).as_posix()])
def sha(data):return hashlib.sha256(data).hexdigest()
cfg=json.loads((R/'tools/model_config.json').read_text())
assert cfg['version']=='v0.1.6'
prior=json.loads(old(R/'reports/release_validation.json'))
assert prior['status']=='pass'
hist=R/'reports/history'/PREVIOUS;hist.mkdir(parents=True,exist_ok=True)
(hist/'release_validation.json').write_bytes(old(R/'reports/release_validation.json'))
(hist/'inventory_entry_validation.json').write_bytes(old(R/'reports/inventory_entry_validation.json'))
unchanged=[]
def archive(kind):
    saved=R/'dist'/f'TianxiangGirlT1Race_{PREVIOUS}_{kind}.zip'
    return zipfile.ZipFile(saved if saved.exists() else R/'dist'/f'TianxiangGirlT1Race_{kind}.zip')
mod_zip=archive('Mod');source_zip=archive('Source')
assert PREVIOUS.encode() in mod_zip.read('TianxiangGirlT1Race/SubModule.xml')
for directory in ['source','tex','module/TianxiangGirlT1Race']:
    for p in (R/directory).rglob('*'):
        if not p.is_file() or p.suffix=='.blend1' or p.name in ['SubModule.xml','TianxiangGirlT1Race.UIRuntime.dll']:continue
        baseline=mod_zip.read(p.relative_to(R/'module').as_posix()) if directory.startswith('module/') else source_zip.read(p.relative_to(R).as_posix())
        assert p.read_bytes()==baseline,p
        unchanged.append(p.relative_to(R).as_posix())
assert sha((R/'module/TianxiangGirlT1Race/AssetPackages/txgirl1.tpac').read_bytes())==prior['final_package_sha256']
prior.update(version=cfg['version'],baseline_package_sha256=prior['final_package_sha256'],
             baseline_reason='Inventory runtime only; source, textures, complete resource package and registration XML match published '+PREVIOUS,
             ui_only_unchanged_files=unchanged,game_test_verified=False)
prior.pop('ui_runtime',None)
prior.pop('module_file_sha256',None)
(R/'reports/release_validation.json').write_text(json.dumps(prior,indent=2))
log=Path('C:/Users/DKX/Documents/Mount and Blade II Bannerlord/TianxiangGirlT1Race/ui_runtime_v0.1.5.jsonl')
records=[json.loads(line) for line in log.read_text().splitlines()]
errors=[r for r in records if r['record'].get('kind')=='error' and 'ActionIndexCache.Equals(Object obj)' in r['record'].get('error','')]
assert errors and not any(r['record'].get('kind')=='tianxiang_pose' for r in records)
evidence=dict(date='2026-10-12',version=cfg['version'],failed_version=PREVIOUS,user_feedback='inventory idle still puts both hands behind back',
              actual_runtime_exception=errors[0],exception_count=len(errors),prior_log_sha256=sha(log.read_bytes()),
              code_failure='Inspect inserts boxed ActionIndexCache into default HashSet<object> before filtering value types; hash collisions call its unchecked Equals(object) and abort the tick',
              actual_prior_inventory_pose_captured=False,
              underlying_idle_pose_cause_not_yet_observed=True,
              fixes=['Collect AgentVisuals-typed tableau fields directly without traversing unrelated fields',
                     'Filter values before seen.Add and use reference identity for cycle detection',
                     'Keep found previews even if secondary discovery fails; skip MapScreen entirely'],
              regression_test='Previous boxed Equals failure reproduced; exact current CollectTableauVisuals, Fields and Inspect methods executed with scoped fixtures',
              new_log='Mount and Blade II Bannerlord/TianxiangGirlT1Race/ui_runtime_v0.1.6.jsonl',
              status='actual_runtime_exception_fixed_offline_game_retest_pending')
(R/'reports/inventory_entry_validation.json').write_text(json.dumps(evidence,indent=2))
print('INVENTORY_UI_ONLY_RESOURCE_PRESERVATION_PASS',len(unchanged))
