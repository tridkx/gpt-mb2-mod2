"""Check rigid high heel shape using final-package data and the v0.1.0 baseline."""
from pathlib import Path
import json,sys,hashlib,subprocess,zipfile,shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[2]
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'))
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
baseline=ROOT/'build/baseline_v0.1.0'
baseline.mkdir(parents=True,exist_ok=True)
if not (baseline/'adar.tpac').exists():
    with zipfile.ZipFile(ROOT/'dist/REAdaWongRace_v0.1.0_Mod.zip') as z:
        (baseline/'adar.tpac').write_bytes(z.read('REAdaWongRace/AssetPackages/adar.tpac'))
if not (baseline/'final_skeleton.json').exists():
    shutil.copy2(ROOT/'reports/history/v0.1.0/final_skeleton.json',baseline/'final_skeleton.json')
subprocess.run([MB,'exportmod',str(baseline/'adar.tpac'),str(baseline/'export'),'0'],check=True,capture_output=True)
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
rig=parse_skeljson(json.loads((ROOT/'reports/final_skeleton.json').read_text()))
oldrig=parse_skeljson(json.loads((baseline/'final_skeleton.json').read_text()))
load=lambda folder:[m for p in (folder/'geo').glob('*.bin') for m in read_geo(p)]
old=load(baseline/'export');new=load(ROOT/'build/final_export_lod0')
old_by_name={m['name']:m for m in old}
assert old_by_name.keys()=={m['name'] for m in new}
for m in new:
    original=old_by_name[m['name']]
    for key in ['pos','uv','idx']:
        assert np.array_equal(original[key],m[key]),('Unrelated final geometry changed',m['name'],key)
    if not m['name'].startswith('adar_legs_boots'):
        for key in ['bi','bw']:assert np.array_equal(original[key],m[key]),('Unrelated weights changed',m['name'])
if (baseline/'fitted_model.npz').exists():
    original=np.load(baseline/'fitted_model.npz');current=np.load(ROOT/'build/fitted_model.npz')
    for key in original.files:
        if key.endswith('_w') and key.startswith('adar_legs_boots'):continue
        assert np.array_equal(original[key],current[key]),('Unrelated source data changed',key)
assert np.max(abs(rig['restWorld'][:,:3,3]-oldrig['restWorld'][:,:3,3]))<1e-6
for i,name in enumerate(rig['names']):
    if name not in ['l_foot','r_foot','l_toe0','r_toe0']:
        assert np.max(abs(rig['restLocal'][i]-oldrig['restLocal'][i]))<1e-6,(name,'Unrelated rig change')
toe_ids={rig['names'].index(n) for n in ['l_toe0','r_toe0']}
lod_checks=[]
for lod in range(4):
    meshes=load(ROOT/f'build/final_export_lod{lod}')
    boots=[m for m in meshes if m['name'].startswith('adar_legs_boots')]
    assert boots
    for m in boots:
        assert not set(m['bi'][m['bw']>0])&toe_ids,(lod,m['name'],'toe influence bends shoe')
        if m['name'].startswith('adar_legs_bootssole'):
            assert (m['bw'].max(1)==255).all()
            for side,pre in [(-1,'l'),(1,'r')]:
                take=m['pos'][:,0]*side>0
                assert (m['bi'][take][m['bw'][take]>0]==rig['names'].index(pre+'_foot')).all()
    lod_checks.append({'lod':lod,'sole_single_foot_bone':True,'boot_toe_influences_absent':True})
motion_checks=[]
for label in ['idle','run','bow','riding','slash']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
    maxerror=0.;framecount=0
    for frame in range(max(1,anim['start']),anim['frames']):
        s=skin_matrices(rig,anim,frame);framecount+=1
        for m in new:
            if not m['name'].startswith('adar_legs_bootssole'):continue
            posed=lbs(m['pos'],m['bi'],m['bw'],s)
            tri=m['idx'].reshape(-1,3)
            edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]])
            base=np.linalg.norm(m['pos'][edges[:,0]]-m['pos'][edges[:,1]],axis=1)
            now=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1)
            maxerror=max(maxerror,float(abs(base-now).max()))
    assert maxerror<1e-6,(label,'Sole/heel changes shape',maxerror)
    motion_checks.append({'motion':label,'frames_checked':framecount,'max_sole_edge_length_error_m':maxerror})
anim=parse_animjson(json.loads((ROOT/'reports/idle.json').read_text()));frame=169
def standing(meshes,skeleton):
    results=[]
    for m in meshes:
        if not m['name'].startswith('adar_legs_bootssole'):continue
        p=m['pos'];posed=lbs(p,m['bi'],m['bw'],skin_matrices(skeleton,anim,frame))
        for side,pre in [(-1,'l'),(1,'r')]:
            heel=(p[:,0]*side>0)&(p[:,1]<-.05)
            toe=(p[:,0]*side>0)&(p[:,1]>.04)
            assert heel.any() and toe.any()
            results.append({'side':pre,'heel_vertical_height_m':float(np.ptp(posed[heel,2])),
                'toe_heel_contact_height_difference_m':float(abs(posed[heel,2].min()-posed[toe,2].min()))})
    return results
before=standing(old,oldrig);after=standing(new,rig)
assert all(x['toe_heel_contact_height_difference_m']<.005 for x in after)
package=ROOT/'module/REAdaWongRace/AssetPackages/adar.tpac'
report={'version':cfg['version'],'status':'pass','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
    'baseline_package_sha256':hashlib.sha256((baseline/'adar.tpac').read_bytes()).hexdigest(),
    'all_final_geometry_and_non_boot_weights_unchanged':True,'original_joint_positions_unchanged':True,
    'lods':lod_checks,'motions':motion_checks,'idle_comparison_frame':frame,'before':before,'after':after,
    'game_IK_ground_contact_verified':False}
(ROOT/'reports/heel_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
