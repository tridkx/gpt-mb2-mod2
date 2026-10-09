"""Compare final files with v0.1.0: resource renaming must preserve geometry."""
import json,sys,subprocess,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe';B=R/'build';checks=[]
for lod in range(4):
 subprocess.run([MB,'exportmod',str(B/'baseline_v0.1.0.tpac'),str(B/f'baseline_export{lod}'),str(lod)],check=True,capture_output=True)
 old={g['name'].lower():g for p in (B/f'baseline_export{lod}/geo').glob('*.bin') for g in read_geo(p)}
 new={g['name']:g for p in (B/f'final_export{lod}/geo').glob('*.bin') for g in read_geo(p)}
 assert set(old)==set(new)
 for name,a in old.items():
  b=new[name]
  for key in ['pos','uv','bi','bw','idx']:assert np.array_equal(a[key],b[key]),(name,key)
  assert a['material']==b['material'] and a['guid']==b['guid'] and a['flags']==b['flags']
 checks.append(dict(lod=lod,groups=len(new),geometry_uv_indices_weights_materials_unchanged=True))
report=dict(version='v0.1.1',status='pass',baseline_sha256=hashlib.sha256((B/'baseline_v0.1.0.tpac').read_bytes()).hexdigest(),checks=checks,repair='lowercase mesh resource names and matching XML references; item IDs retained',cause_status='suspected lookup naming issue; visibility awaits game retest',user_feedback=dict(version='v0.1.0',scope='both A and B outfits invisible when equipped'),game_scale_log=dict(profile='B',immediate_before_after_positions_identical=True,conclusion='immediate snapshot does not establish runtime scale success'),opacity=dict(vertex_alpha_min=255,vertex_alpha_max=255,opaque_materials_present=True))
(R/'reports/visibility_repair.json').write_text(json.dumps(report,indent=2));print('VISIBILITY_REPAIR_VALIDATED')
