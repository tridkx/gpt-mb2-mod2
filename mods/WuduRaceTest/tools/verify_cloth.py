"""Read final native cloth bytes; check roots, mappings, constraints and collision fit."""
import json,sys,subprocess,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build'
sys.path[:0]=[str(WS/'tools'),str(WS/'tools/asset_helpers/previewer'),str(WS/'tools/asset_helpers/tools')]
from georead import read_geo
from cloth_compiler.cloth_payload import read,write,decode_positions
from cloth_compiler.validation import check_structure
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
out=B/'cloth_final';out.mkdir(exist_ok=True)
pkg=R/'module/WuduRaceTest/AssetPackages/wdr.tpac'
data=json.loads(subprocess.check_output(['dotnet',str(B/'cloth_probe/NativeClothProbe.dll'),str(pkg),'wdr_canglan_body','--dump-segments',str(out)],encoding='utf-8'))
assert data[0]['body']=='wdr_canglan_collision'
plans=json.loads((B/'cooked_cloth/manifest.json').read_text());rows=[]
assert len(plans)==10 and {p['lod'] for p in plans}=={0,1}
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
meshes=[json.loads(p.read_text()) for p in out.glob('*.mesh.json') if json.loads(p.read_text())['lod']==0]
poses=[('rest',None,[0])]
render_groups=[g for path in (B/'final_export0/geo').glob('*.bin') for g in read_geo(path) if g['name'].startswith('wdr_part_')]
for label in ['run','idle','bow','rider','sword']:
    animation=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=list(range(animation['start'],animation['frames'])) if label=='run' else sorted(set(np.linspace(animation['start'],animation['frames']-1,16).astype(int)))
    poses.append((label,animation,frames))
for label,anim,frames in poses:
    maximum=0;max_conflict=0;finite=True;worst={}
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
            for point,bone in zip(cap['endpoints_m'],cap['bones']):
                matrix=skin[names.index(bone)];endpoints.append(matrix[:3,:3]@point+matrix[:3,3])
            animated_caps.append((np.array(endpoints),cap['radius_m'],cap['name']))
        for mesh in meshes:
            p=lbs(np.array(mesh['positions']),np.array(mesh['bones']),np.array(mesh['weights']),skin);assert np.isfinite(p).all()
            alpha=np.array(mesh['alpha'])/255;keep=alpha>0
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
    diagnostics.append(dict(pose=label,frames=len(frames),preview_frame=int(worst_frame),max_reference_capsule_overlap_m=maximum,max_travel_shortfall_m=max_conflict,finite=True,worst_by_mesh=worst))
assert max(d['max_travel_shortfall_m'] for d in diagnostics)<=.002, 'Collision and cloth travel conflict exceeds 2 mm screening tolerance'
report=dict(status='pass',travel_shortfall_tolerance_m=.002,final_package_sha256=hashlib.sha256(pkg.read_bytes()).hexdigest(),cooked_meshes=rows,pose_diagnostics=diagnostics,cloth_engine_verified=False,scope='Final payload structure and sampled native-animation capsule/travel screening; overlaps are skinning-reference measurements before the engine cloth solver')
(R/'reports/cloth_validation.json').write_text(json.dumps(report,indent=2))
print('FINAL_CLOTH_VERIFIED',len(rows),'meshes;',diagnostics)
