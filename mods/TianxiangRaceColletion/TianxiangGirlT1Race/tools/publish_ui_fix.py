"""Attest UI-only repair against the published local v0.1.0 baseline."""
from pathlib import Path
import json,subprocess,hashlib,zipfile
R=Path(__file__).resolve().parents[1];W=next(p for p in R.parents if (p/'.git').exists());TAG='TianxiangGirlT1Race/v0.1.0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def old(path):return subprocess.check_output(['git','show',TAG+':'+path.relative_to(W).as_posix()])
report=json.loads(old(R/'reports/release_validation.json'))
hist=R/'reports/history/v0.1.0';hist.mkdir(parents=True,exist_ok=True);(hist/'release_validation.json').write_bytes(old(R/'reports/release_validation.json'))
verified=[]
def archive(kind):
    saved=R/'dist'/f'TianxiangGirlT1Race_v0.1.0_{kind}.zip'
    return zipfile.ZipFile(saved if saved.exists() else R/'dist'/f'TianxiangGirlT1Race_{kind}.zip')
mod_zip=archive('Mod');source_zip=archive('Source')
for base in ['module/TianxiangGirlT1Race','source','tex']:
    for p in (R/base).rglob('*'):
        if not p.is_file() or p.suffix=='.blend1' or p.name in ['SubModule.xml','TianxiangGirlT1Race.UIRuntime.dll']:continue
        if base.startswith('module/'):
            relative=p.relative_to(R/'module').as_posix();baseline=mod_zip.read(relative)
        else:baseline=source_zip.read(p.relative_to(R).as_posix())
        assert p.read_bytes()==baseline,p
        verified.append(p.relative_to(R).as_posix())
dump=Path('C:/Users/DKX/AppData/Local/CrashDumps/TaleWorlds.MountAndBlade.Launcher.exe.3616.dmp')
faults=[t for t in json.loads((R/'build/crash3616_full.json').read_text(encoding='utf-8-sig')) if t['exception']]
evidence=dict(date='2026-10-12',failed_version='v0.1.0',repair_version='v0.1.1',status='ui_scope_risk_fixed_game_retest_pending',pid=3616,dump_path=str(dump),dump_sha256=sha(dump),faults=faults,log='C:/ProgramData/Mount and Blade II Bannerlord/logs/rgl_log_3616.txt',trigger='Inventory screen closed and MapScreen activated at 11:06:16',direct_fault='AccessViolationException in AddWeaponToAgentEntity during AgentVisuals.Refresh',inference='Unrestricted reflective UI scan can reach world/map AgentVisuals and force a UI rebuild. Missing outer managed method names in this minidump prevent complete caller attribution.',fix='Whitelist CharacterTableau/BasicCharacterTableau/BodyGeneratorView owners before reading or refreshing a visual',unchanged_files=verified,game_verified=False)
(R/'reports/map_crash_20261012.json').write_text(json.dumps(evidence,indent=2))
report.update(version='v0.1.1',date='2026-10-12',baseline_package_sha256=report['final_package_sha256'],baseline_reason='UI-only repair; final TPAC/source/cloth/collision compared byte-for-byte with published v0.1.0',game_test_verified=False,ui_scope_unchanged_resource_files=verified)
report['limitations'].append('v0.1.0 user reports crash returning from inventory to campaign map; v0.1.1 preview-owner restriction awaits game retest.')
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
print('UI_ONLY_RESOURCE_PRESERVATION_PASS',len(verified))
