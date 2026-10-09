"""Reuse static poses only after final re-export and byte-preservation proof."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'build/cloth_baseline_v1.0.3'
activation=json.loads((ROOT/'reports/cloth_activation_validation.json').read_text())
release=json.loads((ROOT/'reports/release_validation.json').read_text())
assert activation['status']=='pass' and activation['final_package_sha256']==release['final_package_sha256']
assert activation['all_56_geometry_streams_and_indices_identical']
before=json.loads((BASE/'final_visibility.json').read_text())
after=json.loads((ROOT/'reports/final_visibility.json').read_text())
assert before['materials']==after['materials']
for row in after['meshes']:
 old=next(m for m in before['meshes'] if m['Name']==row['Name'])
 assert old['VertexStreamSHA256']==row['VertexStreamSHA256'] and old['ColorsSHA256']==row['ColorsSHA256']
preview=json.loads((BASE/'final_preview_manifest.json').read_text())
assert preview['package_sha256']==activation['baseline_package_sha256']
for row in preview['previews']:assert (ROOT/row['path']).is_file()
preview['rendered_package_sha256']=preview.get('rendered_package_sha256',preview['package_sha256'])
preview['package_sha256']=release['final_package_sha256']
preview['reuse_basis']='Final TPAC re-export checked. All 56 geometry/index streams, runtime alpha and materials identical to v1.0.3; final textures checked against unchanged build inputs. Own cloth payloads and editor bones added; static previews show no cloth dynamics.'
(ROOT/'reports/final_preview_manifest.json').write_text(json.dumps(preview,indent=2))
print('UNCHANGED_STATIC_PREVIEWS_REUSED_WITH_EXPLICIT_PROVENANCE')
