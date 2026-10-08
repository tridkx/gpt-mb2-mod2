"""Validate hand anchors and forearm/palm deformation on the final TPAC geometry."""
from pathlib import Path
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/tools'))
sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
from hand_fit import forearm_coordinate,posture_fade

def load_meshes(folder):
    return {s['name']:s for file in (folder/'geo').glob('*.bin') for s in read_geo(file)}

def dense_weights(mesh):
    out=np.zeros((len(mesh['pos']),28))
    for slot in range(4):
        np.add.at(out,(np.arange(len(out)),mesh['bi'][:,slot]),mesh['bw'][:,slot]/255.)
    return out

def matched(mesh,positions):
    distance,indices=cKDTree(mesh['pos']).query(positions)
    assert distance.max()<2e-6,(mesh['name'],distance.max())
    return indices

before=np.load(ROOT/'build/grip_baseline/rig_arrays.npz')
after=np.load(ROOT/'build/rig_arrays.npz')
meshes=load_meshes(ROOT/'build/final_export')
old_meshes=load_meshes(ROOT/'build/grip_baseline/export')
rig=parse_skeljson(json.load(open(ROOT/'reports/human_skeleton.json')))
baseline=subprocess.run(['git','show','v1.3.0:module/TianxiangT5/AssetPackages/tx5.tpac'],
                        cwd=ROOT,capture_output=True,check=True).stdout
assert hashlib.sha256(baseline).digest()==hashlib.sha256((ROOT/'build/grip_baseline/tx5.tpac').read_bytes()).digest()
for key in before.files:
    if key in {'source','target','world'} or key.endswith(('_S','_A')):
        assert np.array_equal(before[key],after[key]),key
    if key.startswith(('tx5_head_','tx5_legs_','tx5_body_03')):
        assert np.array_equal(before[key],after[key]),key
# The accepted central torso and shoulder position remain unchanged.
for name in ['tx5_body_00','tx5_body_04']:
    s=after[name+'_S'];keep=np.abs(s[:,0])<.095
    assert np.array_equal(before[name+'_P'][keep],after[name+'_P'][keep]),name
s=after['tx5_body_04_S']
shoulder=(np.abs(s[:,0])>.14)&(s[:,2]>1.29)
assert shoulder.sum()>20
assert np.array_equal(before['tx5_body_04_P'][shoulder],after['tx5_body_04_P'][shoulder])

registered_errors=[];old_errors=[];selections={}
for name in ['tx5_body_07','tx5_body_08']:
    source=after[name+'_S'];new=meshes[name];old=old_meshes[name]
    new_idx=matched(new,after[name+'_P']);old_idx=matched(old,before[name+'_P'])
    nw=dense_weights(new)[new_idx];ow=dense_weights(old)[old_idx]
    palm=np.zeros(len(source),bool);fore=np.zeros(len(source),bool)
    for elbow,twist,wrist,finger,sign in [(17,18,19,20,-1),(24,25,26,27,1)]:
        t,d=forearm_coordinate(source,after['source'][elbow],after['source'][wrist])
        region=(source[:,0]*sign>.27)&(d<.14)&(source[:,2]>.88)
        chosen=region&(t>=1.04)
        palm|=chosen;fore|=region&(t>.25)&(t<.80)
        assert chosen.sum()>20,(name,wrist)
        assert np.all(nw[chosen,wrist]==1),(name,wrist,'palm blended with forearm')
        assert np.all(posture_fade(source[chosen],after['source'],elbow,wrist)==0)
        # Independently reconstruct the hand's unshifted native registration.
        a=after['source'][finger]-after['source'][wrist]
        b=after['target'][finger]-after['target'][wrist]
        aa=a/np.linalg.norm(a);bb=b/np.linalg.norm(b);v=np.cross(aa,bb);c=aa@bb
        k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
        rotation=np.eye(3)+k+k@k/(1+c)
        transform=rotation@(np.eye(3)+(np.linalg.norm(b)/np.linalg.norm(a)-1)*np.outer(aa,aa))
        expected=(source[chosen]-after['source'][wrist])@transform.T+after['target'][wrist]
        registered_errors.extend(np.linalg.norm(new['pos'][new_idx[chosen]]-expected,axis=1).tolist())
        old_errors.extend(np.linalg.norm(old['pos'][old_idx[chosen]]-expected,axis=1).tolist())
    assert (nw[:,[18,25]].sum(1)>0).sum()>40,name
    selections[name]={'new':new,'old':old,'new_w':nw,'old_w':ow,'palm':palm,'fore':fore}
assert max(registered_errors)<2e-6
assert np.median(old_errors)>.10

motion=[]
for label in ['grip_twohanded_pose','grip_twohanded_block','grip_twohanded_thrust','grip_staff_block','bow','riding']:
    raw=json.load(open(ROOT/f'reports/{label}.json'))
    assert sum(len(b['rot']) for b in raw['boneAnims'])>0,label
    anim=parse_animjson(raw)
    frames=range(max(1,anim['start']),anim['frames'])
    before_fore=[];after_fore=[];before_palm=[];after_palm=[]
    for frame in frames:
        skin=skin_matrices(rig,anim,frame)
        for name,selection in selections.items():
            for phase,fore_results,palm_results in [('old',before_fore,before_palm),('new',after_fore,after_palm)]:
                w=selection[phase+'_w']
                # Singular values quantify actual directional compression of the
                # final byte-quantized LBS transform, not a rest-pose weight heuristic.
                sv=np.linalg.svd(np.einsum('vb,bij->vij',w,skin[:,:3,:3]),compute_uv=False)[:,2]
                fore_results.extend(sv[selection['fore']].tolist())
                palm_results.extend(sv[selection['palm']].tolist())
            for mesh in [selection['new'],selection['old']]:
                assert np.isfinite(lbs(mesh['pos'],mesh['bi'],mesh['bw'],skin)).all()
    assert after_palm and min(after_palm)>.9999,(label,min(after_palm))
    old_p5=float(np.percentile(before_fore,5));new_p5=float(np.percentile(after_fore,5))
    assert new_p5>=old_p5-.002,(label,old_p5,new_p5)
    motion.append({'animation':raw['name'],'sampled_frames':len(frames),
                   'forearm_compression_p5_before':old_p5,'forearm_compression_p5_after':new_p5,
                   'palm_min_directional_scale_before':float(min(before_palm)),
                   'palm_min_directional_scale_after':float(min(after_palm))})

# Each LOD must contain valid hand/twist influences and finite normalized geometry.
lods=[]
for lod in range(4):
    data=meshes if lod==0 else load_meshes(ROOT/f'build/final_export_lod{lod}')
    suffix='' if lod==0 else f'.lod{lod}'
    for name in ['tx5_body_07','tx5_body_08']:
        m=data[name+suffix]
        assert np.isfinite(m['pos']).all() and np.all(m['bw'].sum(1)==255)
        assert m['bi'].max()<28
        w=dense_weights(m)
        assert (w[:,[18,25]].sum(1)>0).sum()>0,(name,lod)
        assert (w[:,[19,26]].max(1)==1).sum()>0,(name,lod)
    lods.append(lod)

result={'version':ET.parse(ROOT/'module/TianxiangT5/SubModule.xml').find('Version').get('value'),
        'baseline_version':'v1.3.0','shoulder_setting_degrees':26,
        'central_torso_and_shoulders_unchanged':True,'head_legs_and_skirt_unchanged':True,
        'cloth_vertex_alpha_unchanged':True,'native_hand_bones_unchanged':True,
        'median_previous_hand_registration_offset_mm':float(np.median(old_errors)*1000),
        'max_final_hand_registration_error_mm':float(max(registered_errors)*1000),
        'final_palms_rigid_to_native_hand_bones':True,'lods_checked':lods,'animations':motion,
        'baseline_package_sha256':hashlib.sha256(baseline).hexdigest(),
        'final_package_sha256':hashlib.sha256((ROOT/'module/TianxiangT5/AssetPackages/tx5.tpac').read_bytes()).hexdigest(),
        'game_test_verified':False,
        'limitations':'Offline native skinning only; weapon-specific IK, hand morphs, character scaling and live cloth are not simulated.'}
(ROOT/'reports/grip_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
