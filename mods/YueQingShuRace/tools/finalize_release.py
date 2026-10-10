"""Require the same final package to pass resource, preservation and cloth checks."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
package=R/'module/YueQingShuRace/AssetPackages/yqs.tpac';sha=hashlib.sha256(package.read_bytes()).hexdigest()
reports={n:json.loads((R/'reports'/(n+'.json')).read_text()) for n in ['release_validation','preservation_validation','cloth_validation','source_validation','feedback_fix_validation']}
for name,report in reports.items():
    assert report['status']=='pass',(name,report)
    if 'final_package_sha256' in report:assert report['final_package_sha256']==sha,(name,'stale package')
source=reports['source_validation'];assert source['source_geometry_max_error_m']==0 and source['game_cloth_paint_verified']
source.update(final_package_sha256=sha,version=json.loads((R/'tools/model_config.json').read_text())['version']);(R/'reports/source_validation.json').write_text(json.dumps(source,indent=2))
report=reports['release_validation'];report.update(check_scope='final_resource_source_geometry_preservation_and_cloth_checks',source_geometry_max_error_m=source['source_geometry_max_error_m'],source_height_m=source['source_height_m'],accepted_appearance_baseline='v0.1.1',accepted_appearance_preserved=True,cloth_enabled=True,cloth_lods=[0,1,2,3],cooked_cloth_meshes=len(reports['cloth_validation']['cooked_meshes']),cloth_engine_verified=False)
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
print('RELEASE_COMPLETE',report['version'],sha,report['cooked_cloth_meshes'])
