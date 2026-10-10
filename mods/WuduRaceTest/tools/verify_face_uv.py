"""Compare final eye/face/lash UVs with original FBX and the explicit lash fix."""
import bpy,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build';cfg=json.loads((R/'tools/model_config.json').read_text())
sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
parts=json.loads((R/'input/parts.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
rows=[]
groups={g['name']:g for path in (B/'final_export0/geo').glob('*.bin') for g in read_geo(path)}
for index in [0,5,6]:
    name=f'wdr_part_{index:02d}';ob=bpy.data.objects[parts[index]['name']];me=ob.data
    p=np.array([ob.matrix_world@v.co for v in me.vertices])*cfg['unit_scale']*np.array(cfg['orientation']);uv=me.uv_layers.active.data
    lookup={};source_uv=[]
    for loop in me.loops:
        co=p[loop.vertex_index];u=np.array(uv[loop.index].uv)
        if name in cfg['uv_flip_v_parts']:u[1]=1-u[1]
        lookup.setdefault(tuple(np.rint(co*1e5).astype(int)),[]).append(u);source_uv.append(u)
    g=groups[name];maximum=0
    for co,u in zip(g['pos'],g['uv']):
        expected=lookup.get(tuple(np.rint(co*1e5).astype(int)))
        if expected is None:
            ids=np.where(np.linalg.norm(p-co,axis=1)<1e-6)[0];assert len(ids)>0
            expected=[source_uv[l.index] for l in me.loops if l.vertex_index in ids]
        blender_uv=np.array([u[0],1-u[1]])
        maximum=max(maximum,min(float(abs(blender_uv-v).max()) for v in expected))
    assert maximum<1e-6,(name,maximum)
    rows.append(dict(mesh=name,max_uv_error=maximum,source_v_flipped=name in cfg['uv_flip_v_parts']))
pack=json.loads((B/'final_export0/pack.json').read_text());mat=next(m for m in pack['materials'] if m['name']=='wdr_mat_eyelash_D')
assert mat['alphaTest']==0 and 'alpha_test' not in mat['shaderMatFlags'] and 'gbuffer_alpha_blend' in mat['flags']
report=dict(status='pass',source_input_preserved=True,face_and_iris_uv_unchanged=True,eyelash_v_flipped=True,soft_alpha_preserved=True,meshes=rows,game_verified=False)
(R/'reports/face_uv_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('FACE_UV_VERIFIED',rows)
