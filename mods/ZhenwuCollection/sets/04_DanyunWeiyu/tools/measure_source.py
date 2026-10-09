"""Measure Danyun independently and establish common anatomical coordinates."""
import bpy,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
 return {o.name:{'pos':np.array([o.matrix_world@v.co for v in o.data.vertices]),'uv':np.array([u.uv[:] for u in o.data.uv_layers.active.data])} for o in bpy.data.objects if o.type=='MESH'}
a=load(ROOT.parent/'01_YunhaiNiezong/input/model.fbx');b=load(ROOT/'input/model.fbx');records=[]
for first,second in [('mesh_00_123833','mesh_00_122075'),('mesh_01_142231','mesh_01_140473'),('mesh_04_399558','mesh_04_424248')]:
 p,q=a[first],b[second];pe=float(abs(p['pos']-q['pos']).max());ue=float(abs(p['uv']-q['uv']).max())
 assert pe<1e-5 and ue<1e-6,(second,pe,ue)
 records.append({'first':first,'second':second,'position_error_source_units':pe,'uv_error':ue,'geometry_and_uv_match':True})
for tex in ['eye_D.png','face_D.png','eyelash_D.png','body_D.png']:assert (ROOT/'tex'/tex).read_bytes()==(ROOT.parent/'01_YunhaiNiezong/tex'/tex).read_bytes(),tex
stats=[{'object':n,'vertices':len(v['pos']),'min':v['pos'].min(0).tolist(),'max':v['pos'].max(0).tolist()} for n,v in b.items()]
report={'status':'pass','comparison':records,'matching_anatomical_textures':['eye_D.png','face_D.png','eyelash_D.png','body_D.png'],'independent_bounds':stats,'decision':'Same face, eye and lash coordinates/UV/textures establish identical facial calibration and require the accepted lash V correction. Danyun clothing and body cuts are separately mapped; original inputs remain unchanged.'}
(ROOT/'reports/source_measurement.json').write_text(json.dumps(report,indent=2));print('MEASURED',records)
