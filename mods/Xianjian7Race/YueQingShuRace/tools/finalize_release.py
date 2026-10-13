"""Require the same final package to pass resource, preservation and cloth checks."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
package=R/'module/YueQingShuRace/AssetPackages/yqs.tpac';sha=hashlib.sha256(package.read_bytes()).hexdigest()
reports={n:json.loads((R/'reports'/(n+'.json')).read_text()) for n in ['release_validation','preservation_validation','cloth_validation','source_validation','feedback_fix_validation','settled_skirt_probe']}
for name,report in reports.items():
    assert report['status']=='pass',(name,report)
    if 'final_package_sha256' in report:assert report['final_package_sha256']==sha,(name,'stale package')
source=reports['source_validation'];assert source['source_geometry_max_error_m']==0 and source['game_cloth_paint_verified']
source.update(final_package_sha256=sha,version=json.loads((R/'tools/model_config.json').read_text())['version']);(R/'reports/source_validation.json').write_text(json.dumps(source,indent=2))
report=reports['release_validation'];report['version']=json.loads((R/'tools/model_config.json').read_text())['version'];report.update(check_scope='final_resource_source_geometry_preservation_and_cloth_checks',source_geometry_max_error_m=source['source_geometry_max_error_m'],source_height_m=source['source_height_m'],accepted_appearance_baseline='v0.1.1',accepted_appearance_preserved=True,cloth_enabled=True,cloth_lods=[0,1,2,3],cooked_cloth_meshes=len(reports['cloth_validation']['cooked_meshes']),cloth_engine_verified=False)
acceptance=json.loads((R/'reports/game_acceptance.json').read_text())
report['user_game_acceptance']=dict(version=acceptance['version'],date=acceptance['date'],accepted=acceptance['accepted'],runtime_assets_unchanged=acceptance['package_sha256']==sha,assistant_ran_game=False)
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
print('RELEASE_COMPLETE',report['version'],sha,report['cooked_cloth_meshes'])

for name in ['ui_scope_validation','preview_idle_validation','inventory_pose_validation','arm_binding_validation']:
 item=json.loads((R/'reports'/(name+'.json')).read_text());assert item['status']=='pass';report[name]=item
report['inventory_preview_game_verified']=False
report['user_game_acceptance']['appearance_package_unchanged']=False
report['appearance_geometry_and_materials_preserved']=True
report['arm_bind_axes_corrected']=True
report['user_game_acceptance']['runtime_assets_unchanged']=False
report['user_game_acceptance']['appearance_package_unchanged']=acceptance['package_sha256']==sha
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
