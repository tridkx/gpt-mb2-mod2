"""Check actual final-package sole contact and preserve accepted rig weights."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/tools'));sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
anim=parse_animjson(json.loads((ROOT/'reports/idle.json').read_text()))
manifest=json.loads((ROOT/'build/rig_manifest.json').read_text())
names={r['object'] for r in manifest if r['kind']=='shoe'}
checks=[]
for lod in range(4):
    folder=ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')
    meshes=[m for f in (folder/'geo').glob('*.bin') for m in read_geo(f) if m['name'].split('.lod')[0].split('.b')[0] in names]
    for sign,bone,toe_bone in [(-1,3,4),(1,7,8)]:
        rows=[m for m in meshes if m['pos'][:,0].mean()*sign>0]
        pos=np.concatenate([m['pos'] for m in rows]);bi=np.concatenate([m['bi'] for m in rows]);bw=np.concatenate([m['bw'] for m in rows])
        f=rig['restWorld'][toe_bone,:3,3]-rig['restWorld'][bone,:3,3];f[2]=0;f/=np.linalg.norm(f)
        forward=pos@f;lo,hi=forward.min(),forward.max();heel=forward<lo+(hi-lo)*.25;toe=forward>lo+(hi-lo)*.75
        q=lbs(pos,bi,bw,skin_matrices(rig,anim,1))
        heel_z=float(q[heel,2].min());toe_z=float(q[toe,2].min());floor=float(q[:,2].min())
        assert abs(heel_z-toe_z)<.006,(lod,bone,heel_z,toe_z)
        assert -.001<floor<.006,(lod,bone,floor)
        assert max(heel_z,toe_z)<.009,(lod,bone,heel_z,toe_z)
        idle_gaps=[]
        for frame in [1,45,116,231]:
            q=lbs(pos,bi,bw,skin_matrices(rig,anim,frame));idle_gaps.append(float(q[heel,2].min()-q[toe,2].min()))
        assert max(abs(g) for g in idle_gaps)<.012,(lod,bone,idle_gaps)
        checks.append({'lod':lod,'side':'left' if sign<0 else 'right','reference_frame':1,'heel_height':heel_z,'toe_height':toe_z,
                       'heel_toe_gap':heel_z-toe_z,'lowest_surface':floor,'idle_frames':[1,45,116,231],'idle_heel_toe_gaps':idle_gaps})
old=np.load(ROOT/'build/baseline_v1.0.1/rig_arrays.npz');new=np.load(ROOT/'build/rig_arrays.npz')
weights=[];upper_pants=[]
for r in manifest:
    name=r['object'];assert np.array_equal(old[name+'_W'],new[name+'_W']),name;weights.append(name)
    if r['kind']=='pants':
        mask=old[name+'_P'][:,2]>=.30
        assert np.array_equal(old[name+'_P'][mask],new[name+'_P'][mask]),name
        upper_pants.append({'object':name,'unchanged_vertices_above_30cm':int(mask.sum())})
report={'version':'v1.0.2','status':'pass','final_package_sha256':hashlib.sha256((ROOT/'module/HanfuBlueRed/AssetPackages/hbr.tpac').read_bytes()).hexdigest(),
        'reference':'Final TPAC re-export, byte weights, native inventory standing frame 1','contacts':checks,'unchanged_weight_meshes':weights,
        'upper_pants_preserved':upper_pants,'game_test_verified':False,'limitations':'Native offline skinning only; game foot IK and character sliders require user testing.'}
(ROOT/'reports/shoe_validation.json').write_text(json.dumps(report,indent=2))
print('SHOE_CONTACT_VALIDATED',len(checks),'sides/LODs;',len(weights),'unchanged weight meshes')
