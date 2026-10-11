"""Read delivered skin/bones, exercise every new joint, retain the accepted shape."""
import json, sys, hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];WS=R.parents[1]
sys.path[:0]=[str(WS/'tools/asset_helpers/tools'), str(WS/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import lbs, parse_animjson, q2R
from finger_rig import pose_world
cfg=json.loads((R/'tools/model_config.json').read_text())
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
assert rig['boneCount']==58
baseline=R/'build/finger_baseline_v0.2.6'
source=np.load(R/'build/source_positions.npz')
baseline_checked=False
if (baseline/'source_positions.npz').exists():
    old=np.load(baseline/'source_positions.npz')
    assert set(source.files)==set(old.files) and all(np.array_equal(source[k],old[k]) for k in source.files)
    oldrig=parse_skeljson(json.loads((baseline/'final_skeleton.json').read_text()))
    assert np.max(abs(rig['restWorld'][:28]-oldrig['restWorld']))<1e-6
    baseline_checked=True
rows=[];inverse=np.linalg.inv(rig['restWorld']);poses={}
for lod in range(4):
    meshes=[g for path in (R/f'build/final_export{lod}/geo').glob('*.bin') for g in read_geo(path)]
    hand=next(g for g in meshes if g['name'].split('.lod')[0]=='wdr_part_04')
    p=hand['pos'];bi=hand['bi'];bw=hand['bw'];coverage={}
    for i in range(28,58):
        count=int(np.any((bi==i)&(bw>0),axis=1).sum());assert count>0,(lod,i)
        coverage[rig['names'][i]]=count
    for mesh in meshes:
        if mesh is not hand: assert not np.any((mesh['bi']>=28)&(mesh['bw']>0))
    results=[]
    for left,right in [(0,0),(1,0),(0,1),(.5,.5),(1,1)]:
        posed=lbs(p,bi,bw,pose_world(rig,left,right)@inverse)
        assert np.isfinite(posed).all()
        delta=np.linalg.norm(posed-p,axis=1)
        if left==right==0:assert delta.max()<1e-6
        for sign,value in [(-1,left),(1,right)]:
            change=delta[p[:,0]*sign>0].max()
            assert change>.015 if value else change<1e-6
        results.append(dict(left=left,right=right,max_displacement_m=float(delta.max())))
        if lod==0:poses[f'{left}_{right}']=posed
    # Every added joint must produce movement when individually rotated.
    for i in range(28,58):
        world=rig['restWorld'].copy();local=rig['restLocal'][i].copy();a=.25;c,s=np.cos(a),np.sin(a)
        local[:3,:3]=local[:3,:3]@np.array([[1,0,0],[0,c,-s],[0,s,c]])
        for j in range(i,58):
            if j==i:world[j]=world[rig['parent'][j]]@local
            else:world[j]=world[rig['parent'][j]]@rig['restLocal'][j]
        posed=lbs(p,bi,bw,world@inverse)
        assert np.linalg.norm(posed-p,axis=1).max()>.0005,(lod,rig['names'][i])
    faces=hand['idx'].reshape(-1,3)
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    lengths=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);edges=edges[lengths>1e-5];lengths=lengths[lengths>1e-5]
    closed=lbs(p,bi,bw,pose_world(rig,1,1)@inverse)
    ratios=np.linalg.norm(closed[edges[:,0]]-closed[edges[:,1]],axis=1)/lengths
    assert ratios.max()<2.2,'Finger root stretching exceeds this model screening limit'
    rows.append(dict(lod=lod,vertices=len(p),joint_vertex_coverage=coverage,poses=results,closed_edge_ratio_percentiles=np.percentile(ratios,[1,50,99]).tolist(),closed_edge_ratio_max=float(ratios.max()),edge_ratio_max_tolerance=2.2))
animations=[]
for label in ['idle','run','sword','bow','rider','inventory_idle','facegen_male','facegen_female']:
    anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=range(anim['start'],anim['frames']) if label=='run' else sorted(set(np.linspace(anim['start'],anim['frames']-1,12).astype(int)))
    for frame in frames:
        world=rig['restWorld'].copy()
        for i in range(28):
            local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame]);parent=rig['parent'][i]
            if parent<0:local[:3,3]+=anim['rootPos'][frame]
            world[i]=local if parent<0 else world[parent]@local
        for value in [0,.5,1]:
            assert np.isfinite(lbs(p,bi,bw,pose_world(rig,value,value,world)@inverse)).all()
    animations.append(dict(animation=label,frames=len(frames),grip_values=[0,.5,1]))
np.savez_compressed(R/'build/finger_preview.npz',**poses)
pkg=R/'module/WuduRaceTest/AssetPackages/wdr.tpac'
report=dict(status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256(pkg.read_bytes()).hexdigest(),baseline_package_sha256=hashlib.sha256((baseline/'wdr.tpac').read_bytes()).hexdigest() if (baseline/'wdr.tpac').exists() else None,bones=58,new_finger_joints=30,baseline_compared=baseline_checked,original_vertices_unchanged=baseline_checked,native_28_rest_frames_unchanged=baseline_checked,lods=rows,native_animation_samples=animations,game_verified=False,scope='Final TPAC skeleton and skinning, all 30 joint influences and independent bilateral grip; native runtime update order and weapon contact require user game testing')
(R/'reports/finger_validation.json').write_text(json.dumps(report,indent=2))
print('FINAL_FINGER_RIG_VERIFIED',[(x['lod'],x['vertices']) for x in rows])
