"""Assemble accepted build outputs for the first cumulative release."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
SET=ROOT/'sets/01_YunhaiNiezong'
package=SET/'module/ZhenwuCollection/AssetPackages/zw_yunhai.tpac'
sha=hashlib.sha256(package.read_bytes()).hexdigest()
release=json.loads((SET/'reports/release_validation.json').read_text())
assert release['status']=='pass' and release['final_package_sha256']==sha
for name in ['source_validation','native_provenance','detail_validation','package_audit','eye_uv_validation']:
 report=json.loads((SET/'reports'/(name+'.json')).read_text())
 assert report['status']=='pass',name
 if 'final_package_sha256' in report:assert report['final_package_sha256']==sha,name
preview=json.loads((SET/'reports/final_preview_manifest.json').read_text())
assert preview['package_sha256']==sha
assert preview.get('visually_reviewed') is True,'Final previews must be visually inspected before release'
for p in preview['previews']:assert (SET/p['path']).is_file()
shutil.copytree(SET/'module/ZhenwuCollection',ROOT/'module/ZhenwuCollection',dirs_exist_ok=True)
assert hashlib.sha256((ROOT/'module/ZhenwuCollection/AssetPackages/zw_yunhai.tpac').read_bytes()).hexdigest()==sha
release.update(editable_source_verified=True,all_lod_motion_and_seam_normals_verified=True,visual_review=preview['review_result'],game_test_verified=False)
(SET/'reports/release_validation.json').write_text(json.dumps(release,indent=2))
(ROOT/'reports/release_validation.json').write_text(json.dumps(release,indent=2))
files=['README.md','mod.json']
for folder in ['tools','reports','module','sets/01_YunhaiNiezong']:
 for p in sorted((ROOT/folder).rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(ROOT)
  if any(v in ['build','dist','obj','bin','__pycache__'] for v in rel.parts):continue
  if p.suffix in ['.pyc','.blend1','.blend2','.log'] or p.name=='.gitkeep':continue
  if p.name.startswith('installation_validation'):continue
  if 'module' in rel.parts and p.suffix=='.tpac':continue
  if 'reports' in rel.parts and p.suffix=='.png' and not p.name.startswith('final_'):continue
  files.append(rel.as_posix())
config={'id':'ZhenwuCollection','source_files':sorted(set(files)),'package':'module/ZhenwuCollection/AssetPackages/zw_yunhai.tpac','validation_report':'reports/release_validation.json','included_sets':['01_YunhaiNiezong'],'eighth_set_variant':'PVP'}
(ROOT/'mod.json').write_text(json.dumps(config,indent=2))
print('COLLECTION_DELIVERY_READY',len(config['source_files']),'source files',sha)
