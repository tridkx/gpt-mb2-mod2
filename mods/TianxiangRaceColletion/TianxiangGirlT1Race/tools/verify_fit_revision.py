"""Compare final grip points and collision fit against the accepted v0.1.1."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];B=R/'build'
baseline=json.loads((R/'tools/fit_revision_baseline.json').read_text())
W=next(p for p in R.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R
cfg=json.loads((R/'tools/model_config.json').read_text())
old=baseline['model_config.json']
before=np.load(R/'tools/fit_revision_baseline.npz');after=np.load(B/'fitted_model.npz')
assert set(before.files)==set(after.files)
assert all(np.array_equal(before[k],after[k]) for k in before.files), 'Accepted source geometry or weights changed'
assert all(cfg['landmarks_m'][i]==old['landmarks_m'][i] for i in range(28) if i not in [20,27])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dll=R/'module/TianxiangGirlT1Race/bin/Win64_Shipping_Client/TianxiangGirlT1Race.UIRuntime.dll'
assert sha(dll)==baseline['ui_dll_sha256'], 'Accepted UI repair changed'
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));inv=np.linalg.inv(rig['restWorld'])
p=after['txgirl1_part_06_p'];w=after['txgirl1_part_06_w'];tri=after['txgirl1_part_06_f']
assert (w[:,[20,27]]==0).all(), 'Item bone unexpectedly deforms the hand'
# Densely sample hand triangle interiors, not just sparse fingertip vertices.
samples=[];weights=[]
for a in range(6):
    for b in range(6-a):
        bary=np.array([a,b,5-a-b])/5
        samples.append((p[tri]*bary[None,:,None]).sum(1))
        weights.append((w[tri]*bary[None,:,None]).sum(1))
samples=np.concatenate(samples);weights=np.concatenate(weights)
rows=[]
poses=[('rest',None,[0])]
for label in ['idle','run','bow','riding','slash']:
    anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    frames=range(anim['start'],anim['frames']) if label=='run' else sorted(set(np.linspace(anim['start'],anim['frames']-1,16).astype(int)))
    poses.append((label,anim,frames))
for label,anim,frames in poses:
    distances={side:{'old':[],'new':[]} for side in ['l','r']}
    for frame in frames:
        world=rig['restWorld'].copy()
        if anim is not None:
            for i in range(28):
                local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame]);parent=rig['parent'][i]
                if parent<0:local[:3,3]+=anim['rootPos'][frame]
                world[i]=local if parent<0 else world[parent]@local
        skin=world@inv
        posed=np.zeros_like(samples)
        for bone in range(28):
            posed+=weights[:,bone,None]*(samples@skin[bone,:3,:3].T+skin[bone,:3,3])
        for side,sign,hand,item in [('l',-1,19,20),('r',1,26,27)]:
            keep=(samples[:,0]*sign>.355)&(samples[:,2]<.837)
            tree=cKDTree(posed[keep])
            oldpoint=skin[hand,:3,:3]@np.array(old['landmarks_m'][item])+skin[hand,:3,3]
            newpoint=world[item,:3,3]
            distances[side]['old'].append(float(tree.query(oldpoint)[0]))
            distances[side]['new'].append(float(tree.query(newpoint)[0]))
    rows.append({'pose':label,'frames':len(frames),'surface_distance_m':{side:{key:{'maximum':max(v),'mean':float(np.mean(v))} for key,v in data.items()} for side,data in distances.items()}})
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules']
oldcaps={c['name']:c for c in baseline['cloth_collision.json']['capsules']}
comparison=[{'name':c['name'],'old_radius_m':oldcaps[c['name']]['radius_m'],'new_radius_m':c['radius_m'],'maximum_body_sample_exposure_m':c['maximum_sample_exposure_m']} for c in caps]
assert all(c['new_radius_m']<c['old_radius_m'] and c['maximum_body_sample_exposure_m']==0 for c in comparison)
assert all(row['surface_distance_m'][side]['new']['maximum']<.025 for row in rows for side in ['l','r']), rows
report={'status':'pass','version':cfg['version'],'source_geometry_and_weights_identical':True,'other_joint_positions_identical':True,'accepted_ui_dll_identical':True,'ui_dll_sha256':sha(dll),'grip_target_m':{s:cfg['landmarks_m'][i] for s,i in [('left',20),('right',27)]},'grip_point_distance_to_sampled_hand_surface':rows,'leg_capsule_comparison':comparison,'game_retest_pending':True,'scope':'Item bone origins and sampled skinning surface; does not simulate finger closure, weapon meshes or game cloth solver'}
oldcloth=baseline['cloth_validation.json']['pose_diagnostics']
newcloth=json.loads((R/'reports/cloth_validation.json').read_text())['pose_diagnostics']
report['reference_overlap_comparison']=[{'pose':a['pose'],'old_maximum_m':a['max_reference_capsule_overlap_m'],'new_maximum_m':b['max_reference_capsule_overlap_m']} for a,b in zip(oldcloth,newcloth)]
(R/'reports/fit_revision_validation.json').write_text(json.dumps(report,indent=2))
print('FIT_REVISION_VERIFIED',comparison,rows)
