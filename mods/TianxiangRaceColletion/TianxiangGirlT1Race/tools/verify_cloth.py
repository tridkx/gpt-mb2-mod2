from workspace_paths import workspace_root
"""Read final native cloth bytes; check roots, mappings, constraints and collision fit."""
import json,sys,subprocess,hashlib,shutil
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R=Path(__file__).resolve().parents[1];WS=workspace_root(R);B=R/'build'
sys.path[:0]=[str(WS/'tools'),str(WS/'tools/asset_helpers/previewer'),str(WS/'tools/asset_helpers/tools')]
from georead import read_geo
from cloth_compiler.cloth_payload import read,write,decode_positions
from cloth_compiler.validation import check_structure
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
out=B/'cloth_final';assert out.resolve().parent==B.resolve()
if out.exists():shutil.rmtree(out)
out.mkdir()
pkg=R/'module/TianxiangGirlT1Race/AssetPackages/txgirl1.tpac'
data=json.loads(subprocess.check_output(['dotnet',str(B/'cloth_probe/NativeClothProbe.dll'),str(pkg),'txgirl1_body','--dump-segments',str(out)],encoding='utf-8'))
assert data[0]['body']=='txgirl1_leg_collision'
plans=json.loads((B/'cooked_cloth/manifest.json').read_text());rows=[]
assert plans and {p['lod'] for p in plans}=={0,1}
assert {p['guid'] for p in plans}=={str(m['Guid']) for m in data[0]['meshes'] if 'uses_cloth_simulation' in m['Flags']}
for plan in plans:
    stem=plan['metamesh']+'_'+plan['guid'];raw=(out/(stem+'.bin')).read_bytes();d=read(raw)
    assert hashlib.sha256(raw).hexdigest()==plan['sha256'] and write(d)==raw
    check_structure(d)
    mesh=json.loads((out/(stem+'.mesh.json')).read_text());mapping=d['render_to_sim'];p=np.array(mesh['positions']);nv=d['vertex_count']
    assert np.max(np.linalg.norm(decode_positions(d)[mapping]-p,axis=1))<.00018
    alpha=np.array(mesh['alpha'],float)/255;alpha[plan['solver_pinned_render_vertices']]=0
    assert np.max(abs(d['max_distances'][mapping]-alpha))<1e-6
    assert np.array_equal(d['bone_indices'].reshape(-1,4)[mapping],mesh['bones'])
    assert np.max(abs(d['bone_weights'].reshape(-1,4)[mapping]-np.array(mesh['weights'])/255))<1e-7
    pos=np.zeros((nv,3));pos[mapping]=p;c=d['constraints'];length=np.linalg.norm(pos[c[:,0]]-pos[c[:,1]],axis=1)
    assert np.max(abs(length-d['rest_lengths']))<2e-7
    tri=mapping[np.array(mesh['indices']).reshape(-1,3)];edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])
    _,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(nv,nv)),directed=False)
    assert np.all(labels==labels[d['anchors']>>16])
    assert np.all(labels[c[:,0]]==labels[c[:,1]])
    current=next(x for x in data[0]['meshes'] if x['Guid']==plan['guid'])
    assert current['edit_bones']==current['edit_positions'] and current['UnknownFloat1']==1
    rows.append({k:plan[k] for k in ['mesh','lod','render_vertices','simulation_vertices','active_positions','fixed_positions','stretch_constraints','bend_constraints','root_fixes','sha256']})
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));inverse=np.linalg.inv(rig['restWorld'])
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules'];names=rig['names'];diagnostics=[]
meshes=[json.loads(p.read_text()) for p in out.glob('*.mesh.json') ]
poses=[('rest',None,[0])]
render_groups=[g for path in (B/'final_export_lod0/geo').glob('*.bin') for g in read_geo(path) if g['name'].startswith('txgirl1_part_')]
for label in ['run','idle','bow','riding','slash','stand_unarmed1','stand_unarmed2','stand_unarmed3','stand_onehand','stand_twohand','ui_neutral_male','ui_neutral_female']:
    animation=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=list(range(animation['start'],animation['frames'])) if label=='run' else sorted(set(np.linspace(animation['start'],animation['frames']-1,16).astype(int)))
    poses.append((label,animation,frames))
for label,anim,frames in poses:
    maximum=0;max_conflict=0;max_fixed_overlap=0;finite=True;worst={}
    for frame in frames:
        world=rig['restWorld'].copy()
        if anim is not None:
            for i in range(28):
                local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame]);parent=rig['parent'][i]
                if parent<0:local[:3,3]+=anim['rootPos'][frame]
                world[i]=local if parent<0 else world[parent]@local
        skin=world@inverse
        animated_caps=[]
        for cap in caps:
            endpoints=[]
            for point,weights in zip(cap['endpoints_m'],cap.get('endpoint_weights',[{bone:1.0} for bone in cap['bones']])):
                assert len(weights)<=2 and abs(sum(weights.values())-1)<1e-6
                endpoints.append(sum(weight*(skin[names.index(bone),:3,:3]@point+skin[names.index(bone),:3,3]) for bone,weight in weights.items()))
            animated_caps.append((np.array(endpoints),cap['radius_m'],cap['name']))
        for mesh in meshes:
            p=lbs(np.array(mesh['positions']),np.array(mesh['bones']),np.array(mesh['weights']),skin);assert np.isfinite(p).all()
            alpha=np.array(mesh['alpha'])/255
            plan=next(row for row in plans if row['guid']==mesh['guid']);alpha[plan['solver_pinned_render_vertices']]=0;keep=alpha>0
            for (a,b),radius,capname in animated_caps:
                fixed=p[~keep];axis=b-a;t=np.clip((fixed-a)@axis/max(axis@axis,1e-10),0,1)
                if len(fixed):max_fixed_overlap=max(max_fixed_overlap,float(np.maximum(radius-np.linalg.norm(fixed-a-t[:,None]*axis,axis=1),0).max()))
            if not keep.any():continue
            p=p[keep];penetration=np.zeros(len(p));supplier=np.full(len(p),"",object)
            for (a,b),radius,capname in animated_caps:
                axis=b-a;t=np.clip((p-a)@axis/max(axis@axis,1e-10),0,1)
                current=radius-np.linalg.norm(p-a-t[:,None]*axis,axis=1);supplier[current>penetration]=capname;penetration=np.maximum(penetration,current)
            maximum=max(maximum,float(penetration.max()));conflict=float(np.maximum(penetration-alpha[keep],0).max());max_conflict=max(max_conflict,conflict)
            previous=worst.get(mesh['name'],dict(shortfall_m=-1))
            if conflict>previous['shortfall_m']:worst[mesh['name']]=dict(shortfall_m=conflict,frame=int(frame),overlap_m=float(penetration.max()),worst_capsule=str(supplier[np.argmax(penetration-alpha[keep])]))
    worst_frame=max(worst.values(),key=lambda item:(item['shortfall_m'],item['overlap_m']))['frame']
    world=rig['restWorld'].copy()
    if anim is not None:
        for i in range(28):
            local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,worst_frame]);parent=rig['parent'][i]
            if parent<0:local[:3,3]+=anim['rootPos'][worst_frame]
            world[i]=local if parent<0 else world[parent]@local
    np.savez_compressed(B/(label+'_worst_preview.npz'),**{g['name']:lbs(g['pos'],g['bi'],g['bw'],world@inverse) for g in render_groups})
    diagnostics.append(dict(pose=label,frames=len(frames),preview_frame=int(worst_frame),max_reference_capsule_overlap_m=maximum,max_travel_shortfall_m=max_conflict,max_fixed_root_capsule_overlap_m=max_fixed_overlap,finite=True,worst_by_mesh=worst))
print('FIXED_ROOT_SCREEN',[(d['pose'],d['max_fixed_root_capsule_overlap_m']) for d in diagnostics])
print('CAPSULE_TRAVEL_SCREEN',[(d['pose'],d['max_travel_shortfall_m'],max(d['worst_by_mesh'].items(),key=lambda item:item[1]['shortfall_m'])) for d in diagnostics])
assert max(d['max_travel_shortfall_m'] for d in diagnostics)<=.005, 'Collision and cloth travel conflict exceeds 5 mm screening tolerance'
assert max(d['max_fixed_root_capsule_overlap_m'] for d in diagnostics)<=.005, 'Fixed skirt root intersects the leg capsules'
report=dict(status='pass',travel_shortfall_tolerance_m=.005,final_package_sha256=hashlib.sha256(pkg.read_bytes()).hexdigest(),cooked_meshes=rows,pose_diagnostics=diagnostics,cloth_engine_verified=False,scope='Final payload structure and sampled native-animation capsule/travel screening; overlaps are skinning-reference measurements before the engine cloth solver')
(R/'reports/cloth_validation.json').write_text(json.dumps(report,indent=2))
print('FINAL_CLOTH_VERIFIED',len(rows),'meshes;',diagnostics)
