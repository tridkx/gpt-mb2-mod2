"""Regress running contacts on the final quantized assets, without game physics."""
from pathlib import Path
import json,sys,subprocess,hashlib
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'D:\gpt-mb2-mod\tools')
sys.path.insert(0,r'D:\gpt-mb2-mod\previewer')
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs

def meshes(folder):
    return {s['name']:s for file in (folder/'geo').glob('*.bin') for s in read_geo(file)}

before=meshes(ROOT/'build/movement_baseline/export')
after=meshes(ROOT/'build/final_export')
baseline_bytes=subprocess.run(['git','show','v1.1.1:module/TianxiangT5/AssetPackages/tx5.tpac'],
                              cwd=ROOT,check=True,capture_output=True).stdout
baseline_hash=hashlib.sha256(baseline_bytes).hexdigest()
assert hashlib.sha256((ROOT/'build/movement_baseline/tx5.tpac').read_bytes()).hexdigest()==baseline_hash
rig=parse_skeljson(json.load(open(ROOT/'reports/human_skeleton.json')))
run=parse_animjson(json.load(open(ROOT/'reports/run.json')))
rest=rig['restWorld'][:,:3,3]
frame_skins=[(f,skin_matrices(rig,run,f)) for f in range(max(1,run['start']),run['frames'])]

def contacts(s,legs):
    triangles=s['idx'].reshape(-1,3)
    # Include triangle interiors: testing vertices alone misses wide skirt faces.
    samples=np.r_[s['pos'],s['pos'][triangles].mean(1)]
    keep=samples[:,2]<.90
    aggregate={'capsule_depth_sum_mm':0.,'capsule_max_depth_mm':0.,'capsule_samples_over_1mm':0,
               'surface_depth_sum_mm':0.,'surface_samples_over_1mm':0,'sample_count_per_frame':int(keep.sum())}
    frames=[]
    for frame,skin in frame_skins:
        p=lbs(s['pos'],s['bi'],s['bw'],skin)
        points=np.r_[p,p[triangles].mean(1)][keep]
        gap=np.full(len(points),np.inf)
        for bone,end,radius in [(1,2,.057),(2,3,.040),(3,4,.055),(5,6,.057),(6,7,.040),(7,8,.055)]:
            first=(skin[bone]@np.r_[rest[bone],1])[:3]
            last=(skin[end]@np.r_[rest[end],1])[:3]
            axis=last-first;t=np.clip((points-first)@axis/(axis@axis),0,1)
            gap=np.minimum(gap,np.linalg.norm(points-first-t[:,None]*axis,axis=1)-radius)
        depth=np.maximum(-gap,0)*1000
        aggregate['capsule_depth_sum_mm']+=float(depth.sum())
        aggregate['capsule_max_depth_mm']=max(aggregate['capsule_max_depth_mm'],float(depth.max()))
        aggregate['capsule_samples_over_1mm']+=int((depth>1).sum())
        # A local surface-side estimate, since the source leggings have open seams.
        leg_positions=lbs(legs['pos'],legs['bi'],legs['bw'],skin)
        mesh=trimesh.Trimesh(leg_positions,legs['idx'].reshape(-1,3),process=False)
        closest,distance,face=trimesh.proximity.closest_point(mesh,points)
        signed=np.einsum('ij,ij->i',points-closest,mesh.face_normals[face])
        interior=(signed<-.001)&(distance<.06)
        surface_depth=float(distance[interior].sum()*1000)
        aggregate['surface_depth_sum_mm']+=surface_depth
        aggregate['surface_samples_over_1mm']+=int(interior.sum())
        frames.append({'frame':frame,'capsule_depth_sum_mm':float(depth.sum()),
                       'capsule_max_depth_mm':float(depth.max()),'surface_samples_over_1mm':int(interior.sum())})
    aggregate['frames']=frames
    return aggregate

old=contacts(before['tx5_body_03'],before['tx5_legs_05'])
new=contacts(after['tx5_body_03'],after['tx5_legs_05'])
assert new['capsule_depth_sum_mm']<old['capsule_depth_sum_mm']*.35
assert new['surface_depth_sum_mm']<old['surface_depth_sum_mm']*.60
assert new['capsule_max_depth_mm']<old['capsule_max_depth_mm']

for name in ['tx5_legs_05','tx5_legs_06','tx5_head_01','tx5_head_11','tx5_head_12']:
    for key in ['pos','bi','bw']:assert np.array_equal(before[name][key],after[name][key]),(name,key)
assert all(np.all(s['bw'].sum(1)==255) and s['bi'].max()<28 for s in after.values())

arrays=np.load(ROOT/'build/rig_arrays.npz');prior=np.load(ROOT/'build/movement_baseline/rig_arrays.npz')
source=arrays['tx5_body_07_S'];p=arrays['tx5_body_07_P'];oldp=prior['tx5_body_07_P']
hands=(source[:,2]<1.07)&(np.abs(source[:,0])>.40)
forward_mm=float(np.median((p-oldp)[hands,1])*1000)
assert forward_mm>5,forward_mm
tool=ROOT/'tools/AssetTool/AssetTool.dll'
audit=json.loads(subprocess.run(['dotnet',str(tool),'visibility',str(ROOT/'module/TianxiangT5/AssetPackages/tx5.tpac')],
                               check=True,capture_output=True,text=True).stdout)
assert len(audit['materials'])==9
assert all('disable_vertex_color_alpha' in m['ShaderMaterialFlags'] for m in audit['materials'])
skirt_mesh=next(m for m in audit['meshes'] if m['Name']=='tx5_body_03')
assert skirt_mesh['AlphaMax']<=11 and 'uses_cloth_simulation' in skirt_mesh['Flags']
result={'version':'v1.2.0','baseline_version':'v1.1.1','running_frames':len(frame_skins),
        'baseline_package_sha256':baseline_hash,
        'final_package_sha256':hashlib.sha256((ROOT/'module/TianxiangT5/AssetPackages/tx5.tpac').read_bytes()).hexdigest(),
        'arm_forward_degrees':6,'median_hand_forward_mm_in_rest':forward_mm,
        'before':old,'after':new,
        'capsule_depth_reduction_percent':100*(1-new['capsule_depth_sum_mm']/old['capsule_depth_sum_mm']),
        'surface_depth_reduction_percent':100*(1-new['surface_depth_sum_mm']/old['surface_depth_sum_mm']),
        'skirt_max_distance_m_after_quantization':skirt_mesh['AlphaMax']/255,
        'opacity_fix_preserved':True,'game_cloth_solver_used':False,'game_test_verified':False,
        'method_limit':'Capsules and nearest-surface normals estimate contacts; source leggings have open seams. This is not an in-game collision guarantee.'}
(ROOT/'reports/motion_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['before','after']},indent=2))
print('CONTACT_TOTALS',[(label,{k:v for k,v in check.items() if k!='frames'}) for label,check in [('before',old),('after',new)]])
