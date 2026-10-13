"""Verify transparent lens pass, unchanged assets, and both creation idle rigs."""
from pathlib import Path
import json,sys,subprocess,hashlib,re
import numpy as np
R=Path(__file__).resolve().parents[1];W=R.parents[1]
sys.path[:0]=[str(W/'tools/asset_helpers/tools'),str(W/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs,pose
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
package=R/'module/BoRuRace/AssetPackages/boru_race.tpac';old=R/'build/feedback_baseline/boru_race_v0.1.0.tpac'
if not old.is_file():
    old.parent.mkdir(parents=True,exist_ok=True)
    old.write_bytes(subprocess.check_output(['git','show','BoRuRace/v0.1.0:mods/BoRuRace/module/BoRuRace/AssetPackages/boru_race.tpac']))
def run(args):return subprocess.check_output(args,text=True,encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
details=run([MB,'mat',str(package),'boru_race_glass'])
assert all(flag in details for flag in ['dont_draw_to_gbuffer','no_modify_depth_buffer','alpha_blend_sort','dont_cast_shadow'])
assert 'blendMode=factor' in details and 'renderOrder=1' in details and 'alphaTest=0' in details
assert 'do_not_use_alpha' not in details
assets=[]
# Asset regression uses the prior released TPAC, not the build inputs.
for lod in range(4):
    dest=R/'build/feedback_baseline'/('export_lod'+str(lod));run([MB,'exportmod',str(old),str(dest),str(lod)]+(['--all-mips'] if lod==0 else []))
    current=R/'build'/('final_export_lod'+str(lod))
    before={p.name:sha(p) for p in (dest/'geo').glob('*.bin')};after={p.name:sha(p) for p in (current/'geo').glob('*.bin')}
    assert before==after,('geometry changed',lod)
    assets.append(dict(lod=lod,geometry_bytes_unchanged=True,groups=len(before)))
oldpack=json.loads((R/'build/feedback_baseline/export_lod0/pack.json').read_text());newpack=json.loads((R/'build/final_export_lod0/pack.json').read_text())
assert len(oldpack['textures'])==len(newpack['textures'])
for b,a in zip(oldpack['textures'],newpack['textures']):
    assert b['name']==a['name'] and (R/'build/feedback_baseline/export_lod0'/b['file']).read_bytes()==(R/'build/final_export_lod0'/a['file']).read_bytes()
for p in [R/'source/BoRuRace_Rigged.blend',R/'source/BoRuRace_Rigged.fbx']:
    assert subprocess.check_output(['git','show','BoRuRace/v0.1.0:'+p.relative_to(W).as_posix()])==p.read_bytes()
oldrig=json.loads(subprocess.check_output(['git','show','BoRuRace/v0.1.0:mods/BoRuRace/reports/final_skeleton.json']))
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));baseline=parse_skeljson(oldrig)
assert np.array_equal(rig['restWorld'],baseline['restWorld']) and np.array_equal(rig['parent'],baseline['parent'])
native=parse_skeljson(json.loads((R/'reports/human_skeleton.json').read_text()));ni={n:i for i,n in enumerate(rig['names'])}
meshes=[m for p in (R/'build/final_export_lod0/geo').glob('*.bin') for m in read_geo(p) if not m['name'].startswith('boru_race_hidden')]
arms=[]
for side in ['l','r']:
    ids=[ni[side+'_'+s] for s in ['upperarm_twist','foretwist','hand']]
    def arm_length(skel):return float(sum(np.linalg.norm(skel['restWorld'][b,:3,3]-skel['restWorld'][a,:3,3]) for a,b in zip(ids,ids[1:])))
    arms.append(dict(side=side,source_bind_arm_length_m=arm_length(rig),native_bind_arm_length_m=arm_length(native)))
motions=[]
for label in ['creation_male','creation_female']:
    raw=json.loads((R/'reports'/(label+'.json')).read_text());anim=parse_animjson(raw);assert raw['skeletonGuid']==native['guid']
    jointmax=0.;frame_at=1
    for f in range(max(1,anim['start']),anim['frames']):
        posed=pose(rig,anim,f);assert np.isfinite(posed).all()
        for side in ['l','r']:
            ids=[ni[side+'_'+s] for s in ['upperarm_twist','foretwist','hand']]
            length=sum(np.linalg.norm(posed[b,:3,3]-posed[a,:3,3]) for a,b in zip(ids,ids[1:]))
            source=next(a['source_bind_arm_length_m'] for a in arms if a['side']==side)
            ratio=float(length/source)
            if ratio>jointmax:jointmax=ratio;frame_at=f
    assert jointmax<1.02,(label,'joint length drift',jointmax)
    frames=sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,64).astype(int).tolist()));worst=0.;wf=frames[0];wn=''
    for m in meshes:
        tri=m['idx'].reshape(-1,3);e=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
        lengths=np.linalg.norm(m['pos'][e[:,0]]-m['pos'][e[:,1]],axis=1);valid=lengths>.002;e=e[valid];lengths=lengths[valid]
        for f in frames:
            q=lbs(m['pos'],m['bi'],m['bw'],skin_matrices(rig,anim,f));assert np.isfinite(q).all()
            ratio=np.linalg.norm(q[e[:,0]]-q[e[:,1]],axis=1)/lengths
            v=float(ratio.max()) if len(ratio) else 0
            if v>worst:worst=v;wf=f;wn=m['name']
    assert worst<6,(label,worst,wn)
    motions.append(dict(label=label,asset=raw['name'],frames_checked=len(frames),joint_frames_checked=anim['frames']-max(1,anim['start']),total_frames=anim['frames'],worst_frame=wf,worst_mesh=wn,max_edge_extension=worst,max_arm_joint_length_ratio=jointmax))
report=dict(status='pass',version='v0.1.1',date='2026-10-13',baseline_version='v0.1.0',baseline_package_sha256=sha(old),final_package_sha256=sha(package),all_lod_geometry_weight_bytes_unchanged=assets,all_texture_mip_bytes_unchanged=True,source_blend_fbx_bytes_unchanged=True,bind_skeleton_unchanged=True,arms=arms,creation_motion_checks=motions,lens_material_details=details,ui_scope_report='reports/ui_scope_validation.json',game_retest_verified=False,inference='Screenshot shows character creation; old owner gate excludes that view and Native rebuild omits ActionSet. Correcting the UI skeleton is the repair candidate, pending game verification.',material_evidence='Lens had factor blending and alpha 51 but lacked forward-pass/depth flags. Added dont_draw_to_gbuffer, no_modify_depth_buffer, sorted pass and render order 1; game transparency remains to be verified.')
(R/'reports/feedback_fix_validation.json').write_text(json.dumps(report,indent=2))
release=json.loads((R/'reports/release_validation.json').read_text());release['baseline_package_sha256']=sha(old);release['baseline_reason']='BoRuRace v0.1.0 before UI/lens repair';release['feedback_fix_validation']='reports/feedback_fix_validation.json';release['motions']=[m for m in release['motions'] if not m['label'].startswith('creation_')]+motions
(R/'reports/release_validation.json').write_text(json.dumps(release,indent=2))
print('FEEDBACK_FIX_CHECKS_PASS',arms,motions)
