"""Prepare actual delivery manifest after package and editable-source QA."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report_path=ROOT/'reports/release_validation.json';report=json.loads(report_path.read_text())
source=json.loads((ROOT/'reports/source_validation.json').read_text());assert source['status']=='pass'
package=ROOT/'module/TianxiangRenqiu/AssetPackages/rq1.tpac'
assert report['status']=='pass' and report['final_package_sha256']==hashlib.sha256(package.read_bytes()).hexdigest()
preview=json.loads((ROOT/'reports/final_preview_manifest.json').read_text());assert preview['package_sha256']==report['final_package_sha256']
report['editable_source_verified']=True
report['visual_review']={'reviewed':'final eye/lash close-ups, rest front/side/back and worst native motion/contact frames','result':'reviewed with offline limitations','game_verified':False}
report_path.write_text(json.dumps(report,indent=2))
files=['README.md','mod.json']
if (ROOT/'CHANGELOG.md').is_file():files.append('CHANGELOG.md')
for folder in ['input','source','tools','module','reports']:
    for p in sorted((ROOT/folder).rglob('*')):
        if not p.is_file() or any(part in ['__pycache__','obj','bin'] for part in p.relative_to(ROOT).parts):continue
        if p.name=='.gitkeep' or p.suffix in ['.pyc','.blend1','.log']:continue
        if folder=='module' and p.suffix=='.tpac':continue
        if folder=='reports' and p.suffix=='.png' and not p.name.startswith('final_'):continue
        files.append(p.relative_to(ROOT).as_posix())
cfg={'id':'TianxiangRenqiu','source_files':files,'package':'module/TianxiangRenqiu/AssetPackages/rq1.tpac','validation_report':'reports/release_validation.json'}
(ROOT/'mod.json').write_text(json.dumps(cfg,indent=2))
print('DELIVERY_MANIFEST_READY',len(files),'files plus textures')
