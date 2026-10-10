"""Transfer the installed native 26 hand-pose channels onto this model's hands."""
import json,sys,subprocess
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build'
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
cfg=json.loads((R/'tools/model_config.json').read_text());K=cfg['unit_scale']/.01

def load_native():
    subprocess.run(['dotnet','build',str(R/'tools/HandProbe/HandProbe.csproj'),'--ignore-failed-sources','-o',str(B/'hand_probe')],check=True)
    native_pkg='D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/EmAssetPackages/human/human.tpac'
    subprocess.run(['dotnet',str(B/'hand_probe/HandProbe.dll'),native_pkg,'hands_female_a',str(B/'native_hands.json')],check=True)
    return next(m for m in json.loads((B/'native_hands.json').read_text()) if m['Lod']==0)

def morph_positions(points,native):
    rig=parse_skeljson(json.loads((R/'reports/human_skeleton.json').read_text()))
    rot=rig['restWorld'][26,:3,:3];native_wrist=rig['restWorld'][26,:3,3]
    scale=np.array(cfg['hand_rig']['native_local_scale']);offset=np.array(cfg['hand_rig']['native_local_offset_m'])
    original_wrist=np.array([.38,0,.82]);base=np.array(native['edit_positions'])[:,:3]
    result=np.repeat(points[None,:,:],26,axis=0)
    assert len(native['frames'])==26
    for sign in [-1,1]:
        src_ids=np.where(base[:,0]*sign>0)[0];dst_ids=np.where(points[:,0]*sign>0)[0]
        mirror=np.array([sign,1,1]);src=base[src_ids]*mirror
        local=(src-native_wrist)@rot
        mapped_local=local*scale+offset
        def smooth(a,b,x):
            t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
        thumb=smooth(.047,.068,mapped_local[:,2])*(1-smooth(.045,.060,mapped_local[:,0]))
        mapped_local[:,0]-=.024*thumb
        mapped=mapped_local@rot.T+original_wrist
        target=points[dst_ids]/K*mirror
        distance,index=cKDTree(mapped).query(target,k=6)
        weight=1/np.maximum(distance,.0015)**3;weight/=weight.sum(axis=1,keepdims=True)
        # Keep the proximal wrist contour fixed for all shape channels.
        axial=(target-original_wrist)@rot[:,0]
        t=np.clip((axial+.004)/.026,0,1);pin=t*t*(3-2*t)
        lateral=(target-original_wrist)@rot[:,2]
        pin=np.maximum(pin,smooth(.043,.059,lateral)*(1-smooth(.036,.055,axial)))
        for frame,f in enumerate(native['frames']):
            delta=(np.array(f['positions'])[src_ids,:3]-base[src_ids])*mirror
            delta=((delta@rot)*scale)@rot.T
            interpolated=np.sum(delta[index]*weight[:,:,None],axis=1)
            result[frame,dst_ids]+=interpolated*pin[:,None]*mirror*K
    return result

def normals_for(p,faces,base):
    area=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
    normal=np.zeros_like(p)
    for corner in range(3):np.add.at(normal,faces[:,corner],area)
    length=np.linalg.norm(normal,axis=1);keep=length>1e-12
    normal[keep]/=length[keep,None];normal[~keep]=base[~keep]
    return normal

if __name__=='__main__':
    native=load_native();output={};summary=[]
    for row in json.loads((B/'geometry.json').read_text()):
        if row['part']!='hands':continue
        raw=Path(row['geometry']).read_bytes();_,count,_=np.frombuffer(raw,'<i4',3);p=np.frombuffer(raw,'<f4',count*3,12).reshape(-1,3).astype(float)
        normal=np.frombuffer(raw,'<f4',count*3,12+count*12).reshape(-1,3).astype(float)
        faces=np.frombuffer(raw,'<u4',offset=12+count*(3+3+4+2+2)*4+count*12).reshape(-1,3)
        frames=morph_positions(p,native);assert np.isfinite(frames).all() and np.array_equal(frames[0],p)
        output[row['name']]=[dict(time=int(native['frames'][i]['Time']),positions=x.tolist(),normals=(normal if i==0 else normals_for(x,faces,normal)).tolist()) for i,x in enumerate(frames)]
        summary.append(dict(mesh=row['name'],lod=row['lod'],vertices=int(count),channels=26,max_displacement_m=float(np.linalg.norm(frames-p,axis=2).max())))
    (B/'hand_morphs.json').write_text(json.dumps(output))
    source=np.load(B/'source_positions.npz')['wdr_part_04_p'];np.savez_compressed(B/'hand_source_shapes.npz',frames=morph_positions(source,native))
    (R/'reports/hand_morph_build.json').write_text(json.dumps(dict(version=cfg['version'],native_template='hands_female_a',channels=26,meshes=summary,method='Local anatomical scale and nearest-surface displacement transfer with pinned wrist',game_verified=False),indent=2))
    print('HAND_MORPHS_READY',summary)
