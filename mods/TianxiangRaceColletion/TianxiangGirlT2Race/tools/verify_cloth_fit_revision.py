"""Compare final LOD0 authored shape and unaffected binding with v0.1.0."""
import json,hashlib,sys
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);sys.path.insert(0,str(W/'tools/asset_helpers/tools'))
from georead import read_geo
baseline=json.loads((R/'tools/cloth_fit_baseline.json').read_text());sha=lambda a:hashlib.sha256(a.tobytes()).hexdigest()
meshes={g['name']:g for p in (R/'build/final_export_lod0/geo').glob('*.bin') for g in read_geo(p)};rows=[]
assert set(meshes)==set(baseline['meshes'])
for name,g in meshes.items():
    old=baseline['meshes'][name];same={key:sha(g[key])==old[key] for key in old}
    assert all(same[key] for key in ['pos','uv','idx']),(name,same)
    if name!='txgirl2_part_12':assert all(same.values()),(name,same)
    rows.append(dict(mesh=name,source_geometry_uv_topology_unchanged=True,weight_bytes_unchanged=same['bi'] and same['bw']))
report=dict(status='pass',version=json.loads((R/'tools/model_config.json').read_text())['version'],baseline_package_sha256=baseline['package_sha256'],final_package_sha256=hashlib.sha256((R/'module/TianxiangGirlT2Race/AssetPackages/txgirl2.tpac').read_bytes()).hexdigest(),meshes=rows,allowed_changes='Skirt covering flaps/panels/attached ornaments continuous hip binding; skirt Alpha/cooked constraints; model capsules; release version and diagnostic log name')
(R/'reports/cloth_fit_revision_validation.json').write_text(json.dumps(report,indent=2));print('CLOTH_REVISION_PASS',report['version'])
