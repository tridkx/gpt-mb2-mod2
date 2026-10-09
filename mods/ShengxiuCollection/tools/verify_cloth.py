"""Verify the delivered cloth fields and anchor-distance channels, no solver."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1]
WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
PACKAGE=ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
def read(command):return json.loads(subprocess.check_output(['dotnet',str(WS/'tools/AssetTool/AssetTool.dll'),command,str(PACKAGE)],text=True,encoding='utf-8'))
vis=read('visibility');meta=read('inspect')
plan={'sx_mingyu_head_00':('long_hair',.025),'sx_mingyu_body_06':('skirt',.09),'sx_mingyu_body_13':('sleeve_veils',.16)}
rows=[]
for mm in meta:
 assert mm['UnknownString']=='human_body'
 for mesh in mm['meshes']:
  channel=next(x for x in vis['meshes'] if x['Name']==mesh['Name'])
  active=mesh['Name'] in plan
  assert ('uses_cloth_simulation' in mesh['Flags'])==active
  if not active:assert channel['AlphaMax']==0
  else:
   kind,limit=plan[mesh['Name']]
   assert mesh['Lod']==0 and channel['AlphaMin']==0 and 0<channel['AlphaMax']<=round(limit*255)
   material=mesh['ClothingMaterial']
   assert material['BendingStiffness']==.35 and material['StretchingStiffness']==1 and material['AnchorStiffness']==1
   assert material['Damping']==.48 and material['Gravity']==7
   rows.append({'mesh':mesh['Name'],'region':kind,'alpha_byte_range':[channel['AlphaMin'],channel['AlphaMax']],
                'maximum_distance_m':channel['AlphaMax']/255,'fixed_anchor_vertices_present':True,'cloth_material':material})
assert {r['mesh'] for r in rows}==set(plan)
cloth=next(m for m in vis['materials'] if m['Name']=='sx_mingyu_cloth')
assert cloth['AlphaTest']==.025 and 'disable_vertex_color_alpha' in cloth['ShaderMaterialFlags']
report={'status':'pass','final_package_sha256':hashlib.sha256(PACKAGE.read_bytes()).hexdigest(),'scope':'Final TPAC metadata and vertex alpha only; no game cloth solver or tcc/tcm cooking',
        'cloth_meshes':rows,'cloth_material_visibility':cloth,'game_solver_verified':False,'collision_reference':'human_body; in-game capsule response not verified'}
(ROOT/'reports/cloth_validation.json').write_text(json.dumps(report,indent=2))
print('FINAL_CLOTH_FIELDS_VERIFIED',len(rows),'meshes')
