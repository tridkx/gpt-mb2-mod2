"""Final-source guards for the model-specific combined tunic and skirt."""
import bpy,sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangSuimeng_Rigged.blend'))
a=np.load(ROOT/'build/rig_arrays.npz');name='sm6_body_08';o=bpy.data.objects[name];source=a[name+'_S'];w=a[name+'_W'];alpha=a[name+'_A'];parent=list(range(len(source)))
def find(v):
    while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
    return v
for e in o.data.edges:parent[find(e.vertices[1])]=find(e.vertices[0])
panels={}
for v in range(len(source)):panels.setdefault(find(v),[]).append(v)
cfg=json.loads((ROOT/'tools/model_config.json').read_text());torso=[];skirt=[]
for ids in panels.values():
    q=source[ids];is_skirt=q[:,2].max()<cfg['mixed_skirt_component_max_z'] and q[:,2].mean()<cfg['mixed_skirt_component_mean_z']
    (skirt if is_skirt else torso).extend(ids)
assert len(torso)>500 and len(skirt)>300
assert np.all(alpha[torso]==0);assert np.all(w[:,14:]==0),'combined central tunic must not inherit hand/forearm'
assert w[skirt][:,[2,6]].max()>.1 and alpha[skirt].max()>0
assert ((w>1e-6).sum(1)<=4).all()
release=json.loads((ROOT/'reports/release_validation.json').read_text());assert release['status']=='pass'
digest=hashlib.sha256((ROOT/'module/TianxiangSuimeng/AssetPackages/sm6.tpac').read_bytes()).hexdigest();assert digest==release['final_package_sha256']
report={'status':'pass','final_package_sha256':digest,'torso_vertices':len(torso),'skirt_vertices':len(skirt),'torso_cloth_pinned':True,'central_tunic_hand_and_forearm_weights':0,'calf_follow_enabled':True,'four_bone_limit':True,'game_verified':False}
(ROOT/'reports/mixed_tunic_validation.json').write_text(json.dumps(report,indent=2));print('MIXED_TUNIC_VERIFIED',report)
