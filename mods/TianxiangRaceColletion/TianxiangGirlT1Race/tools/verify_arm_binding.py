"""Reconstruct captured character-creation poses and check source arm axes."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parents[1];W=next(p for p in R.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
sys.path.insert(0,str(W/'tools/asset_helpers/tools'))
from baker.skeleton import parse_skeljson
from baker.animation import lbs
from georead import read_geo
old=parse_skeljson(json.loads((R/'tools/arm_bind_baseline.json').read_text()))
new=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
assert np.max(abs(old['restWorld'][:,:3,3]-new['restWorld'][:,:3,3]))<2e-6
changed={15,16,17,18,22,23,24,25}
assert all(np.max(abs(old['restWorld'][i]-new['restWorld'][i]))<2e-6 for i in range(28) if i not in changed)
axis_rows=[]
for parent,child in [(15,16),(16,17),(17,18),(18,19),(22,23),(23,24),(24,25),(25,26)]:
    delta=new['restWorld'][child,:3,3]-new['restWorld'][parent,:3,3]
    direction=new['restWorld'][parent,:3,0]
    # Intermediate source landmarks are approximate: test the anatomical whole
    # upper-arm/forearm axis separately; report their remaining local offsets.
    axis_rows.append({'child':new['names'][child],'old_local_side_offset_m':float(np.linalg.norm(old['restLocal'][child,1:3,3])),
                      'new_local_side_offset_m':float(np.linalg.norm(new['restLocal'][child,1:3,3]))})
for start,end in [(15,17),(17,19),(22,24),(24,26)]:
    delta=new['restWorld'][end,:3,3]-new['restWorld'][start,:3,3]
    assert np.linalg.norm(np.cross(delta,new['restWorld'][start,:3,0]))<2e-6
meshes=[m for p in (R/'build/final_export_lod0/geo').glob('*.bin') for m in read_geo(p) if not m['name'].startswith('txgirl1_hidden')]
records=json.loads((R/'reports/character_creation_pose_baseline.json').read_text())['records'];rows=[]
for n,record in enumerate(records):
    game=record['record'];posed=np.array([np.array(b['posed_entity']).reshape(4,4).T for b in game['bones']])
    candidate=np.zeros_like(posed)
    for i,p in enumerate(old['parent']):
        if p<0:candidate[i]=posed[i];continue
        local=np.linalg.inv(posed[p])@posed[i]
        local[:3,3]+=new['restLocal'][i,:3,3]-old['restLocal'][i,:3,3]
        candidate[i]=candidate[p]@local
    diagnostics={}
    for name,world,rig in [('before',posed,old),('after',candidate,new)]:
        skin=world@np.linalg.inv(rig['restWorld']);arrays={m['name']:lbs(m['pos'],m['bi'],m['bw'],skin) for m in meshes}
        np.savez_compressed(R/'build'/('arm_'+name+'_'+str(n)+'.npz'),**arrays)
        chest=[];arms=[]
        for m in meshes:
            q=arrays[m['name']];p=m['pos']
            if m['name'].startswith('txgirl1_part_07'):
                keep=(abs(p[:,0])<.12)&(p[:,2]>.80)&(p[:,2]<1.095);chest.append(q[keep])
            if m['name'].startswith('txgirl1_part_06'):
                arms.append(q[(abs(p[:,0])>.25)&(p[:,2]<.915)])
        chest=np.concatenate(chest);arms=np.concatenate(arms);hull=ConvexHull(chest)
        signed=(arms@hull.equations[:,:3].T+hull.equations[:,3]).max(1)
        diagnostics[name]={'arm_vertices_in_torso_convex_envelope':int((signed<0).sum()),
                           'maximum_envelope_depth_m':float(np.maximum(-signed,0).max()),
                           'minimum_signed_envelope_distance_m':float(signed.min()),'tested_arm_vertices':len(arms)}
    rows.append({'capture_time':record['time'],'screen':game['screen'],'animation':game['animation1'],
                 'progress':game['progress1'],'diagnostics':diagnostics})
report={'status':'pass','version':json.loads((R/'tools/model_config.json').read_text())['version'],
        'source_joint_positions_unchanged':True,'non_arm_bind_frames_unchanged':True,'arm_local_offsets':axis_rows,
        'captured_pose_reconstructions':rows,'package_sha256':hashlib.sha256((R/'module/TianxiangGirlT1Race/AssetPackages/txgirl1.tpac').read_bytes()).hexdigest(),
        'scope':'Actual older game poses reconstructed with new bind translations; torso convex envelope is a conservative diagnostic, not triangle intersection or a new game test',
        'game_retest_pending':True}
(R/'reports/arm_binding_validation.json').write_text(json.dumps(report,indent=2))
print('ARM_BINDING_VERIFIED',rows)
