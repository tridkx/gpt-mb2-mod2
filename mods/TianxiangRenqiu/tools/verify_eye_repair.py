"""Compare every final mesh to preserved v1.0.0; only lash V/tangent may change."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'build/eye_baseline_v1.0.0'
sys.path.insert(0,str(ROOT.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
def read(folder):return {m['name']:m for f in folder.glob('*.bin') for m in read_geo(f)}
old=json.loads((BASE/'final_visibility.json').read_text());new=json.loads((ROOT/'reports/final_visibility.json').read_text())
oldm={m['Name']:m for m in old['meshes']};newm={m['Name']:m for m in new['meshes']};assert oldm.keys()==newm.keys()
changed=[]
for name,m in newm.items():
    b=oldm[name]
    for field in ['Material','Flags','Vertices','ColorsSHA256','ClothMetadataSHA256']:assert m[field]==b[field],(name,field)
    if m['VertexStreamSHA256']!=b['VertexStreamSHA256']:
        assert name.split('.')[0]=='rq1_head_03',name
        changed.append(name)
assert len(changed)==4,changed
for lod in range(4):
    oldgeo=read(BASE/f'geo_lod{lod}');newgeo=read(ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')/'geo')
    assert oldgeo.keys()==newgeo.keys()
    for name,m in newgeo.items():
        b=oldgeo[name]
        for field in ['pos','idx','bi','bw']:assert np.array_equal(m[field],b[field]),(name,field)
        if name.split('.')[0]=='rq1_head_03':
            assert np.array_equal(m['uv'][:,0],b['uv'][:,0])
            assert np.max(abs(m['uv'][:,1]-(1-b['uv'][:,1])))<1e-6
        else:assert np.array_equal(m['uv'],b['uv']),name
lash=next(m for m in new['materials'] if m['Name']=='rq1_lash')
assert lash['BlendMode']=='no_alpha_blend' and abs(lash['AlphaTest']-.4)<1e-6
assert {'alpha_test','disable_vertex_color_alpha'}<=set(lash['ShaderMaterialFlags'])
eye=next(m for m in new['materials'] if m['Name']=='rq1_eye');assert eye==next(m for m in old['materials'] if m['Name']=='rq1_eye')
for mat in new['materials']:
    if mat['Name']!='rq1_lash':assert mat==next(m for m in old['materials'] if m['Name']==mat['Name'])
result={'status':'pass','baseline_version':'v1.0.0','changed_uv_meshes':changed,'positions_indices_weights_unchanged_all_60_meshes':True,'cloth_and_vertex_colors_unchanged':True,'eye_material_unchanged':True,'lash_material':lash,'game_verified':False}
(ROOT/'reports/eye_repair_validation.json').write_text(json.dumps(result,indent=2))
f=ROOT/'reports/release_validation.json';r=json.loads(f.read_text());r['eye_repair']=result;f.write_text(json.dumps(r,indent=2));print('EYE_REPAIR_VERIFIED',changed)
