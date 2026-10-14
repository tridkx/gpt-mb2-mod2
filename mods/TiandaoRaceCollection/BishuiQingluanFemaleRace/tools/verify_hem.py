"""Verify sleeve simulation is absent and upper skirt release is smooth."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
from skirt_policy import travel
R=Path(__file__).resolve().parents[1];W=workspace_root(R);B=R/'build';sys.path.insert(0,str(W/'tools/cloth_compiler'))
from cloth_payload import read
from mapping_payload import read as read_map
cfg=json.loads((R/'tools/model_config.json').read_text());h=cfg['mapped_cloth']['hem_policy'];visibility=json.loads((R/'reports/final_visibility.json').read_text());sleeves=[m for m in visibility['meshes'] if m['Name'].startswith('bql_part_13')];assert len(sleeves)==4 and all('uses_cloth_simulation' not in m['Flags'] for m in sleeves)
source=json.loads((B/'proxy_source.json').read_text());assert not any('sleeve' in k or k=='bql_part_13' for k in json.loads((B/'proxy_branches.json').read_text()))
plan=json.loads((B/'mapped_proxy_cooked/manifest.json').read_text())[0];d=read(Path(plan['path']));n=len(source['skirt_vertices']);p=np.array(source['positions'])[:n];a=np.array(source['alpha'])[:n];assert (a[p[:,2]>=h['fixed_above_z_m']]==0).all();assert (a[p[:,2]<h['transition_end_z_m']]>0).all();assert np.array_equal(a,np.rint(np.where(travel(p[:,2],h)<.004,0,travel(p[:,2],h))*255).astype(int))
profiles=[]
for z in [1.045,.80,.72,.68,.64,.60,.56,.52,.48,.40,.30,.20,.117]:profiles.append(dict(height_m=z,maximum_activity_m=float(travel(np.array([z]),h)[0])))
maps=json.loads((B/'mapped_render_maps/manifest.json').read_text());inputs={json.loads(p.read_text())['guid']:json.loads(p.read_text()) for p in (B/'cloth_final').glob('*.mesh.json')};assert not any(m['name'].startswith('bql_part_13') for m in inputs.values());rows=[]
from cloth_regions import skirt_mask
raw=np.load(B/'fitted_model.npz')
for item in maps:
 m=inputs[item['guid']]
 if not m['name'].startswith('bql_part_09'):continue
 p=np.array(m['positions']);sk=skirt_mask('bql_part_09',p,np.array(m['indices']).reshape(-1,3),raw);a=np.array(m['alpha']);upper=sk&(p[:,2]>=h['fixed_above_z_m']);assert not a[upper].any();rows.append(dict(lod=m['lod'],stable_upper_vertices=int(upper.sum()),active_hem_vertices=int((sk&(a>0)).sum())))
package=R/'module'/cfg['id']/'AssetPackages/bql.tpac';report=dict(status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),sleeve_simulation_enabled=False,sleeve_lods_checked=4,policy=h,profiles=profiles,lods=rows,upper_skirt_is_skinned=True,transition='smoothstep multiplied by distance below fixed boundary, then byte quantized',game_verified=False)
(R/'reports/hem_policy_validation.json').write_text(json.dumps(report,indent=2));print('HEM_POLICY_VERIFIED',rows,profiles)
