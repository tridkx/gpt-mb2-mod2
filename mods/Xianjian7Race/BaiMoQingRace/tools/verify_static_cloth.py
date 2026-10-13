"""Check disabled native cloth and exact v0.1.0 GPU geometry preservation."""
from pathlib import Path
import json,subprocess,hashlib,sys
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text());ident=cfg['id'];prefix=cfg['prefix'];pkg=R/'module'/ident/'AssetPackages'/(prefix+'.tpac')
assert not cfg['cloth_enabled']
subprocess.run(['dotnet',str(R/'build/disable_cloth/DisableCloth.dll'),str(pkg),'--verify',prefix],check=True)
for lod in range(4):
 old=R/'build/baseline_v0.1.0_exports'/f'lod{lod}';new=R/'build'/f'final_export_lod{lod}';a={p.name:p for p in (old/'geo').glob('*.bin')};b={p.name:p for p in (new/'geo').glob('*.bin')};assert a.keys()==b.keys()
 for name,path in a.items():assert path.read_bytes()==b[name].read_bytes(),('GPU stream changed',lod,name)
 op=json.loads((old/'pack.json').read_text());np=json.loads((new/'pack.json').read_text());assert op['materials']==np['materials'] and op['skeletons']==np['skeletons']
 if lod==0:
  for texture in op['textures']:assert (old/texture['file']).read_bytes()==(new/texture['file']).read_bytes()
report=dict(status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256(pkg.read_bytes()).hexdigest(),all_lods_cloth_flags_removed=True,cooked_cloth_payloads_removed=True,cloth_collision_references_removed=True,gpu_streams_exactly_equal_to_v0_1_0=True,materials_textures_skeleton_preserved=True,game_test_verified=False)
(R/'reports/static_cloth_validation.json').write_text(json.dumps(report,indent=2));print('STATIC_CLOTH_VERIFIED',ident)
