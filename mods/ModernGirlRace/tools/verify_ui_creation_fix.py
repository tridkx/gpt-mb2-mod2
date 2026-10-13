"""Verify the local UI contract and unchanged v0.1.0 character assets."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
BUILD = ROOT / 'build/ui_creation_contract'
BUILD.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

baseline = json.loads((ROOT / 'reports/ui_creation_fix_baseline.json').read_text())
allowed = {
    'module/ModernGirlRace/SubModule.xml',
    'module/ModernGirlRace/bin/Win64_Shipping_Client/ModernGirlRace.UIRuntime.dll',
}
unchanged = [name for name, digest in baseline.items() if sha(ROOT / name) == digest]
changed = sorted(set(baseline) - set(unchanged))
assert set(changed) == allowed, changed

def decompile(module, assembly, type_name):
    dll = GAME / 'Modules' / module / 'bin/Win64_Shipping_Client' / assembly
    result = subprocess.run(['ilspycmd', '-t', type_name, str(dll)],
                            check=True, capture_output=True, text=True, encoding='utf-8')
    (BUILD / (type_name.rsplit('.', 1)[-1] + '.cs')).write_text(result.stdout, encoding='utf-8')
    return result.stdout

body = decompile('Native', 'TaleWorlds.MountAndBlade.GauntletUI.dll',
                 'TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView')
screen = decompile('Sandbox', 'SandBox.View.dll',
                   'SandBox.View.CharacterCreation.CharacterCreationScreen')
stage = decompile('Sandbox', 'SandBox.GauntletUI.dll',
                  'SandBox.GauntletUI.CharacterCreation.CharacterCreationFaceGeneratorView')
assert 'private AgentVisuals _visualToShow;' in body
assert 'private AgentVisuals _nextVisualToShow;' in body
assert '_currentStageView;' in screen and 'private BodyGeneratorView _faceGeneratorView;' in stage
initial = body[body.index('AgentVisualsData data'):body.index('AgentVisualsData data') + 1400]
assert '.ActionSet(' in initial and '"_facegen"' in initial
rebuild = body[body.index('private void RefreshCharacterEntityAux()'):]
rebuild_data = rebuild[rebuild.index('AgentVisualsData data'):rebuild.index('AgentVisuals obj')]
assert '.ActionSet(' not in rebuild_data
assert 'GetActionAtChannel' in rebuild and 'GetAnimationParameterAtChannel' in rebuild
scope = json.loads((ROOT / 'reports/ui_scope_validation.json').read_text())
assert scope['status'] == 'pass' and scope['creation_rebuilding_visuals_collected']
assert scope['correct_skeleton_wrong_set_repaired'] and scope['matching_preview_idempotent']
runtime = ROOT / 'tools/UIRuntime/Runtime.cs'
dll = ROOT / 'module/ModernGirlRace/bin/Win64_Shipping_Client/ModernGirlRace.UIRuntime.dll'
assert sha(runtime) == scope['source_sha256'] and sha(dll) == scope['assembly_sha256']
report = dict(status='pass', date='2026-10-13', version='v0.1.1',
              baseline_version='v0.1.0', changed_module_files=changed,
              unchanged_assets=unchanged, final_runtime_sha256=sha(dll),
              local_game_contract_verified=True,
              initial_facegen_action_set_present=True,
              native_rebuild_action_set_missing=True,
              current_and_next_visuals_covered=True,
              matching_skeleton_wrong_action_set_covered=True,
              native_action_mappings_unchanged=True,
              game_verified=False,
              diagnosis='Native body-generator rebuild omits ActionSet; old runtime excluded this owner and never repaired the fallback warrior preview.')
(ROOT / 'reports/ui_creation_fix_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('UI_CREATION_CONTRACT_AND_ASSET_PRESERVATION_PASS', len(unchanged), 'unchanged files')
