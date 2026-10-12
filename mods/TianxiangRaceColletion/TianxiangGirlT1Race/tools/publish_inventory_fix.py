"""Attest the scoped inventory runtime repair against published v0.1.4."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
W=next(p for p in R.parents if (p/'.git').exists())
TAG='TianxiangGirlT1Race/v0.1.4'
def old(p):
    return subprocess.check_output(['git','show',TAG+':'+p.relative_to(W).as_posix()])
def sha(data):return hashlib.sha256(data).hexdigest()
cfg=json.loads((R/'tools/model_config.json').read_text())
assert cfg['version']=='v0.1.5'
prior=json.loads(old(R/'reports/release_validation.json'))
assert prior['status']=='pass'
hist=R/'reports/history/v0.1.4';hist.mkdir(parents=True,exist_ok=True)
(hist/'release_validation.json').write_bytes(old(R/'reports/release_validation.json'))
unchanged=[]
def archive(kind):
    saved=R/'dist'/f'TianxiangGirlT1Race_v0.1.4_{kind}.zip'
    return zipfile.ZipFile(saved if saved.exists() else R/'dist'/f'TianxiangGirlT1Race_{kind}.zip')
mod_zip=archive('Mod');source_zip=archive('Source')
assert b'v0.1.4' in mod_zip.read('TianxiangGirlT1Race/SubModule.xml')
for directory in ['source','tex','module/TianxiangGirlT1Race']:
    for p in (R/directory).rglob('*'):
        if not p.is_file() or p.suffix=='.blend1' or p.name in ['SubModule.xml','TianxiangGirlT1Race.UIRuntime.dll']:continue
        baseline=mod_zip.read(p.relative_to(R/'module').as_posix()) if directory.startswith('module/') else source_zip.read(p.relative_to(R).as_posix())
        assert p.read_bytes()==baseline,p
        unchanged.append(p.relative_to(R).as_posix())
assert sha((R/'module/TianxiangGirlT1Race/AssetPackages/txgirl1.tpac').read_bytes())==prior['final_package_sha256']
prior.update(version=cfg['version'],baseline_package_sha256=prior['final_package_sha256'],
             baseline_reason='Inventory runtime only; source, textures, complete resource package and registration XML match published v0.1.4',
             ui_only_unchanged_files=unchanged,game_test_verified=False)
prior.pop('ui_runtime',None)
prior.pop('module_file_sha256',None)
(R/'reports/release_validation.json').write_text(json.dumps(prior,indent=2))
log=Path('C:/Users/DKX/Documents/Mount and Blade II Bannerlord/TianxiangGirlT1Race/ui_runtime_v0.1.1.jsonl')
records=[json.loads(line) for line in log.read_text().splitlines()]
inventory=[r for r in records if r.get('session')=='20261012_160112' and r['record'].get('screen')=='SandBox.GauntletUI.GauntletInventoryScreen']
assert inventory and all(r['record'].get('visuals')==0 for r in inventory if r['record'].get('kind')=='scan')
evidence=dict(date='2026-10-12',version=cfg['version'],failed_version='v0.1.4',user_feedback='inventory idle still puts both hands behind back',
              prior_inventory_scans=inventory,prior_log_sha256=sha(log.read_bytes()),
              code_risk='Screen traversal exhausts the shared seen budget before the inventory texture provider is visited',
              actual_prior_inventory_pose_captured=False,
              fixes=['Read CharacterTableauTextureProvider directly before screen traversal with independent seen budget',
                     'Skip only when skeleton and expected action set both match','Log real action names; sample each screen independently'],
              new_log='Mount and Blade II Bannerlord/TianxiangGirlT1Race/ui_runtime_v0.1.5.jsonl',
              status='offline_entry_and_scope_checked_game_retest_pending')
(R/'reports/inventory_entry_validation.json').write_text(json.dumps(evidence,indent=2))
print('INVENTORY_UI_ONLY_RESOURCE_PRESERVATION_PASS',len(unchanged))
