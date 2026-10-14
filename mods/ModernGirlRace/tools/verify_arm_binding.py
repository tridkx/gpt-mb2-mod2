"""Verify final arm bind axes and unchanged non-target mesh data against v0.1.1."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];W=R.parents[1]
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
sys.path.insert(0,str(W/'tools/asset_helpers/tools'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,pose
from georead import read_geo
old=parse_skeljson(json.loads((R/'reports/arm_bind_baseline.json').read_text()))
new=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
assert old['names']==new['names'] and np.array_equal(old['parent'],new['parent'])
assert np.max(abs(old['restWorld'][:,:3,3]-new['restWorld'][:,:3,3]))<2e-6
changed={15,16,17,18,22,23,24,25}
assert all(np.max(abs(old['restWorld'][i]-new['restWorld'][i]))<2e-6 for i in range(28) if i not in changed)
rows=[]
for i,a,b in [(15,15,17),(16,15,17),(17,17,19),(18,17,19),(22,22,24),(23,22,24),(24,24,26),(25,24,26)]:
    v=new['restWorld'][b,:3,3]-new['restWorld'][a,:3,3];v/=np.linalg.norm(v)
    angles=[float(np.degrees(np.arccos(np.clip((rig['restWorld'][i,:3,0]/np.linalg.norm(rig['restWorld'][i,:3,0]))@v,-1,1)))) for rig in [old,new]]
    assert angles[1]<.02
    rows.append(dict(bone=new['names'][i],before_degrees=angles[0],after_degrees=angles[1]))
baseline=json.loads((R/'reports/arm_repair_baseline.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(R/f)==h for f,h in baseline['source_sha256'].items())
digest=lambda a:hashlib.sha256(a.tobytes()).hexdigest()
after=np.load(R/'build/fitted_model.npz')
for k,h in baseline['source_array_sha256'].items():
    if not k.endswith('_w') or k!='modern_girl_part_02_w':
        assert digest(after[k])==h,k
for lod,expected in baseline['final_mesh_array_sha256'].items():
    current={m['name']:m for p in (R/f'build/final_export_lod{lod}/geo').glob('*.bin') for m in read_geo(p)}
    assert current.keys()==expected.keys()
    for name,hashes in expected.items():
        for k,h in hashes.items():
            if k in ['bi','bw'] and name.startswith('modern_girl_part_02'):continue
            assert digest(current[name][k])==h,(lod,name,k)
B=R/'build/arm_repair_baseline'
weight_changes=None
if B.exists():
    before=np.load(B/'fitted_model.npz');after=np.load(R/'build/fitted_model.npz')
    assert set(before.files)==set(after.files)
    assert all(np.array_equal(before[k],after[k]) for k in before.files if not k.endswith('_w'))
    weight_changes={k:int(np.any(abs(before[k]-after[k])>1e-7,axis=1).sum()) for k in before.files if k.endswith('_w')}
    assert all(n==0 for k,n in weight_changes.items() if k not in ['modern_girl_part_02_w','modern_girl_part_03_w','modern_girl_part_04_w'])
    for lod in range(4):
        def meshes(folder):return {m['name']:m for p in folder.glob('*.bin') for m in read_geo(p)}
        a=meshes(B/f'lod{lod}');b=meshes(R/f'build/final_export_lod{lod}/geo');assert a.keys()==b.keys()
        for name in a:
            for key in ['pos','uv','idx']:
                assert np.array_equal(a[name][key],b[name][key]),(lod,name,key)
            if not name.startswith('modern_girl_part_02'):
                for key in ['bi','bw']:
                    assert np.array_equal(a[name][key],b[name][key]),(lod,name,key)
motions=[]
for label in ['idle','run','bow','riding','slash','facegen','stand_unarmed','stand_1h','stand_2h']:
    path=R/'reports'/(label+'.json')
    if not path.exists():continue
    data=json.loads(path.read_text());native=json.loads((R/'reports/human_skeleton.json').read_text())
    assert data['skeletonGuid']==native['guid']
    anim=parse_animjson(data);frames=range(max(1,anim['start']),anim['frames'])
    spans={}
    for name,rig in [('before',old),('after',new)]:
        spans[name]=[float(np.linalg.norm(pose(rig,anim,f)[19,:3,3]-pose(rig,anim,f)[26,:3,3])) for f in frames]
    motions.append(dict(label=label,asset=data['name'],frames=len(spans['after']),before_min_wrist_span_m=min(spans['before']),after_min_wrist_span_m=min(spans['after'])))
report=dict(status='pass',version=json.loads((R/'tools/model_config.json').read_text())['version'],date='2026-10-14',package_sha256=sha(R/'module/ModernGirlRace/AssetPackages/modern_girl.tpac'),baseline_package_sha256=baseline['package_sha256'],axes=rows,joints_and_non_arm_bind_frames_preserved=True,source_geometry_preserved=True,weight_change_scope='Shirt shoulder transfer band and shared sleeve attachment points',final_geometry_uv_indices_preserved_all_lods=True,input_textures_runtime_preserved=True,motions=motions,game_retest_pending=True,scope='Final TPAC bind axes and native animation diagnostics; wrist span does not certify absence of intersections, IK or weapon grip.')
report['changed_source_weight_vertices']=weight_changes
report['non_shirt_final_weights_preserved_all_lods']=True
(R/'reports/arm_binding_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('ARM_BINDING_VERIFIED',json.dumps(rows),json.dumps(motions))
