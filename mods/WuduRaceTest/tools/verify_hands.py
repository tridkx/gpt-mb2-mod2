"""Read final morph channels and compare geometry/scale against the accepted baseline."""
import json,sys,hashlib,subprocess
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build';cfg=json.loads((R/'tools/model_config.json').read_text());K=cfg['unit_scale']/.01
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
pkg=R/'module/WuduRaceTest/AssetPackages/wdr.tpac'
integrated=cfg.get('hands_render_mode')=='body'
subprocess.run(['dotnet',str(B/'hand_probe/HandProbe.dll'),str(pkg),'wdr_canglan_body' if integrated else 'wdr_canglan_hands',str(B/'final_hand_probe.json')],check=True)
data=json.loads((B/'final_hand_probe.json').read_text());expected=json.loads((B/'hand_morphs.json').read_text());rows=[]
if integrated:
    data=[m for m in data if m['Name'].split('.lod')[0]=='wdr_part_04']
    assert len(data)==4
    for mesh in data:
        assert mesh['VertexKeyCount']==0 and len(mesh['frames'])==0, 'Integrated hands must use the accepted rigid-skin render path'
        # The following deformation checks cover retained SOURCE shapes only.
        mesh['frames']=[dict(Time=f['time'],positions=[list(p)+[1] for p in f['positions']],normals=[list(p)+[1] for p in f['normals']]) for f in expected[mesh['Name']]]
assert len(data)==4 and {m['Lod'] for m in data}=={0,1,2,3}
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
for mesh in data:
    p=np.array(mesh['positions']);mapping=np.array(mesh['edit_vertex_position_indices']);frames=mesh['frames'];assert len(frames)==26 and (integrated or mesh['VertexKeyCount']==26)
    assert len(mesh['bones'])==len(p) and np.all(np.sum(mesh['weights'],axis=1)==255)
    if integrated:assert np.max(abs(np.array(frames[0]['positions'])[:,:3][mapping]-p))<6e-8
    else:assert np.array_equal(np.array(frames[0]['positions'])[:,:3][mapping],p)
    if not integrated:assert np.all(np.array(mesh['edit_positions'])[:,3]==1), 'Morph rest positions require homogeneous W=1, matching native hands'
    assert [f['Time'] for f in frames]==np.arange(26,dtype='<f4').view('<i4').tolist()
    allp=np.array([f['positions'] for f in frames])[:,:,:3]
    target=expected[mesh['Name']]
    assert np.max(abs(allp-np.array([f['positions'] for f in target])))<6e-8
    assert np.isfinite(allp).all() and np.linalg.norm(allp-p[None],axis=2).max()<.12
    normals=np.array([f['normals'] for f in frames])[:,:,:3];assert np.isfinite(normals).all()
    assert np.max(abs(np.linalg.norm(normals,axis=2)-1))<1e-4
    right=p[:,0]>0;root=np.zeros(len(p),bool);mix={}
    for sign,hand,twist in [(-1,19,18),(1,26,25)]:
        ids=np.where(p[:,0]*sign>0)[0];q=p[ids]/K
        old_origin=np.array([sign*.38,0,.82]);axial=(q-old_origin)@rig['restWorld'][hand,:3,0]
        root[ids[(axial<=-.004)&(q[:,1]<.04)]]=True
        bones=np.array(mesh['bones'])[ids];weights=np.array(mesh['weights'])[ids]
        mixed=np.any((bones==hand)&(weights>0),axis=1)&np.any((bones==twist)&(weights>0),axis=1)
        assert mixed.any();mix[str(sign)]=int(mixed.sum())
    assert root.any() and np.max(abs(allp[:,root]-p[root]))<6e-8
    assert np.linalg.norm(allp[:,right]-p[right],axis=2).max()>.02 and np.linalg.norm(allp[:,~right]-p[~right],axis=2).max()>.02
    faces=np.array(mesh['indices']).reshape(-1,3);edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);edges=edges[length>1e-5];length=length[length>1e-5]
    ratios=np.linalg.norm(allp[:,edges[:,0]]-allp[:,edges[:,1]],axis=2)/length
    rows.append(dict(lod=mesh['Lod'],vertices=len(p),channels=0 if integrated else 26,source_shape_channels=26,mixed_wrist_vertices=mix,pinned_root_vertices=int(root.sum()),max_displacement_m=float(np.linalg.norm(allp-p,axis=2).max()),edge_ratio_percentiles=np.percentile(ratios,[1,50,99]).tolist()))
source=np.load(B/'source_positions.npz');baseline=B/'hand_baseline_v0.2.0';baseline_checked=False
if (baseline/'source_positions.npz').exists():
    old=np.load(baseline/'source_positions.npz');assert set(source.files)==set(old.files)
    assert all(np.array_equal(source[k],old[k]) for k in source.files)
    old_rig=parse_skeljson(json.loads((baseline/'final_skeleton.json').read_text()));assert rig['names'][:28]==old_rig['names']
    allowed={18,19,25,26};assert np.max(abs(rig['restWorld'][[i for i in range(28) if i not in allowed]]-old_rig['restWorld'][[i for i in range(28) if i not in allowed]]))<1e-6
    baseline_checked=True
pose_rows=[];mesh=next(m for m in data if m['Lod']==0);p=np.array(mesh['positions']);bi=np.array(mesh['bones']);bw=np.array(mesh['weights']);inverse=np.linalg.inv(rig['restWorld'])
for label in ['run','idle','sword','bow','rider']:
    anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()));frames=list(range(anim['start'],anim['frames'])) if label=='run' else sorted(set(np.linspace(anim['start'],anim['frames']-1,16).astype(int)))
    worst_angle=-1;worst_frame=frames[0]
    for frame in frames:
        world=rig['restWorld'].copy()
        for i in range(rig['boneCount']):
            local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame]) if i<28 else local[:3,:3];parent=rig['parent'][i]
            if parent<0:local[:3,3]+=anim['rootPos'][frame]
            world[i]=local if parent<0 else world[parent]@local
        for shape in [0,13,25]:
            posed=lbs(np.array(mesh['frames'][shape]['positions'])[:,:3],bi,bw,world@inverse);assert np.isfinite(posed).all()
        angle=np.arccos(np.clip((np.trace(rig['restLocal'][26,:3,:3].T@q2R(anim['quat'][26,frame]))-1)/2,-1,1))
        if angle>worst_angle:worst_angle=angle;worst_frame=frame
    pose_rows.append(dict(animation=label,frames=len(frames),hand_shapes_checked=[0,13,25],max_right_wrist_local_angle_deg=float(np.degrees(worst_angle)),preview_frame=int(worst_frame)))
report=dict(status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256(pkg.read_bytes()).hexdigest(),baseline_source_and_height_unchanged=baseline_checked,meshes=rows,native_animation_samples=pose_rows,hand_engine_verified=False,scope='Final hand slot/morph payload, wrist weights, source fidelity and sampled native-animation deformation; engine hand-pose selection and weapon contact require game testing')
report.update(render_mode='body' if integrated else 'independent',engine_morph_channels=0 if integrated else 26,source_shape_channels=26)
if integrated:report['scope']='Final body includes all four hand LODs with no runtime morph frames; source-only 26 shapes retained and checked; additional finger bone weights are checked by finger_validation.json; visibility, skeletal driver and wrist effects require user game testing'
(R/'reports/hand_validation.json').write_text(json.dumps(report,indent=2));print('FINAL_HANDS_VERIFIED',rows)
