"""Final package cloth channels and per-region profiles; no engine solver."""
from pathlib import Path
import json,hashlib,subprocess,numpy as np
ROOT=Path(__file__).resolve().parents[1];WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
PACKAGE=ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
def read(command):return json.loads(subprocess.check_output(['dotnet',str(WS/'tools/AssetTool/AssetTool.dll'),command,str(PACKAGE)],text=True,encoding='utf-8'))
vis=read('visibility');meta=read('inspect');cfg=json.loads((ROOT/'tools/model_config.json').read_text(encoding='utf-8'))
recipe=json.loads((ROOT/'build/cloth_recipe.json').read_text());rows=[]
for mm in meta:
 assert mm['UnknownString']=='human_body'
 for mesh in mm['meshes']:
  channel=next(x for x in vis['meshes'] if x['Name']==mesh['Name'])
  name=mesh['Name'];active=name in recipe[mm['Name']]
  assert ('uses_cloth_simulation' in mesh['Flags'])==active
  if not active:assert channel['AlphaMax']==0
  else:
   planned=recipe[mm['Name']][name]['profile']
   assert channel['AlphaMin']==0 and channel['AlphaMax']>0
   assert mesh['UnknownFloat1']==planned['UnknownFloat1']
   for key,value in planned['material'].items():assert mesh['ClothingMaterial'][key]==value,(name,key)
   rows.append({'mesh':name,'lod':mesh['Lod'],'alpha_byte_range':[channel['AlphaMin'],channel['AlphaMax']],
    'reader_unknown_float1':mesh['UnknownFloat1'],'cloth_material':mesh['ClothingMaterial']})
assert {r['mesh'] for r in rows}=={'sx_mingyu_head_00','sx_mingyu_body_06','sx_mingyu_body_13','sx_mingyu_body_13.lod1'}
before=json.loads((ROOT/'build/cloth_baseline_v1.0.1/final_cloth.json').read_text())
for mm in meta:
 old=next(x for x in before if x['Name']==mm['Name'])
 for mesh in mm['meshes']:
  if mesh['Name'] not in ['sx_mingyu_body_13','sx_mingyu_body_13.lod1']:assert mesh==next(x for x in old['meshes'] if x['Name']==mesh['Name'])
cloth=next(m for m in vis['materials'] if m['Name']=='sx_mingyu_cloth')
assert cloth['AlphaTest']==.025 and 'disable_vertex_color_alpha' in cloth['ShaderMaterialFlags']
plan=json.loads((ROOT/'reports/veil_distance_plan.json').read_text());assert len(plan['panels'])==6
for panel in plan['panels']:
 assert len(panel['fixed_vertices'])>=2 and max(panel['painted_alpha'])<=1
 assert sum(a==0 for a in panel['painted_alpha'])==len(panel['fixed_vertices'])
report={'status':'pass','final_package_sha256':hashlib.sha256(PACKAGE.read_bytes()).hexdigest(),
 'scope':'Final TPAC metadata and byte-alpha; no game solver or tcc/tcm cooking',
 'cloth_meshes':rows,'cloth_material_visibility':cloth,'game_solver_verified':False,
 'fixed_veil_panels':len(plan['panels']),'unrelated_cloth_metadata_preserved':True,
 'unknown_float1_interpretation':'Candidate distance scale inferred from reader layout; editor equivalence not proven on this game version'}
(ROOT/'reports/cloth_validation.json').write_text(json.dumps(report,indent=2))
print('FINAL_CLOTH_FIELDS_VERIFIED',len(rows),'meshes, 6 pinned panels')
