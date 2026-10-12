"""T2 final-byte protection samples and pose-space capsule evaluation."""
import json,sys,numpy as np
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path[:0]=[str(W/'tools/asset_helpers/tools'),str(W/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
cfg=json.loads((R/'tools/model_config.json').read_text())
bones=json.loads((R/'build/skeleton_spec.json').read_text())
rig=parse_skeljson({'bones':[dict(b,i=i) for i,b in enumerate(bones)]});inverse=np.linalg.inv(rig['restWorld'])
def native_skins(samples=32):
    yield 'rest',0,np.tile(np.eye(4),(28,1,1))
    for label in ['run','idle','bow','riding','slash','stand_unarmed1','stand_unarmed2','stand_unarmed3','stand_onehand','stand_twohand','ui_neutral_male','ui_neutral_female']:
        anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
        frames=range(anim['start'],anim['frames']) if label=='run' else sorted(set(np.linspace(anim['start'],anim['frames']-1,samples).astype(int)))
        for frame in frames:
            world=rig['restWorld'].copy()
            for i in range(28):
                local=rig['restLocal'][i].copy();local[:3,:3]=q2R(anim['quat'][i,frame]);parent=rig['parent'][i]
                if parent<0:local[:3,3]+=anim['rootPos'][frame]
                world[i]=local if parent<0 else world[parent]@local
            yield label,int(frame),world@inverse
    recorded=json.loads((R/'reports/captured_creation_poses_v0.1.0.json').read_text())['records']
    for n,row in enumerate(recorded):
        world=np.array([np.array(b['posed_entity']).reshape(4,4).T for b in row['bones']])
        yield 'captured_creation',n,world@inverse

def protection_mesh(authored=False):
    for file in ([] if authored else (R/'build/final_export_lod0/geo').glob('*.bin')):
        for g in read_geo(file):
            if g['name']==cfg['shorts_part']:return g
    # Clean source-package rebuild: parse the freshly authored byte geometry.
    data=(R/'build/mesh'/(cfg['shorts_part']+'.mgeo')).read_bytes()
    magic,nv,ni=np.frombuffer(data,'<i4',3);assert magic==0x4f45474d
    offset=12;fields={}
    for name,width,dtype in [('pos',3,'<f4'),('normal',3,'<f4'),('tangent',4,'<f4'),('uv',2,'<f4'),('uv2',2,'<f4'),('color',4,'u1'),('bi',4,'u1'),('bw',4,'u1')]:
        fields[name]=np.frombuffer(data,dtype,nv*width,offset).reshape(nv,width).copy();offset+=nv*width*np.dtype(dtype).itemsize
    fields['idx']=np.frombuffer(data,'<u4',ni,offset).copy();return fields
def surface_samples(mesh,skin,grid=7):
    f=mesh['idx'].reshape(-1,3)
    bary=np.array([[i,j,grid-1-i-j] for i in range(grid) for j in range(grid-i)])/(grid-1)
    rest=np.einsum('bq,tqc->tbc',bary,mesh['pos'][f]).reshape(-1,3)
    lo,hi=cfg['shorts_height_band_m'];mask=(rest[:,2]>lo)&(rest[:,2]<hi)
    posed=lbs(mesh['pos'],mesh['bi'],mesh['bw'],skin)
    return np.einsum('bq,tqc->tbc',bary,posed[f]).reshape(-1,3)[mask]
def endpoints(cap,skin):
    weights=cap.get('endpoint_weights',[{b:1.0} for b in cap['bones']])
    return np.array([sum(w*(skin[rig['names'].index(n),:3,:3]@point+skin[rig['names'].index(n),:3,3]) for n,w in ws.items()) for point,ws in zip(cap['endpoints_m'],weights)])
def outside_union(points,caps,skin):
    outside=np.full(len(points),1e9)
    for c in caps:
        a,b=endpoints(c,skin);v=b-a;t=np.clip((points-a)@v/max(v@v,1e-10),0,1)
        outside=np.minimum(outside,np.linalg.norm(points-a-t[:,None]*v,axis=1)-c['radius_m'])
    return outside

def published_capsules():
    import xml.etree.ElementTree as ET
    path=R/'module/TianxiangGirlT2Race/ModuleData/cloth_bodies.xml'
    body=ET.parse(path).getroot().find('body');assert body.get('name')=='txgirl2_leg_collision' and body.get('owner_skeleton')==cfg['skeleton']
    result=[]
    for cap in body.findall('./capsules/capsule'):
        frame=np.array([float(x) for x in cap.get('frame').split(',')]).reshape(4,4).T
        a=frame[:3,3];b=a+frame[:3,0]*float(cap.get('length'))
        points=cap.findall('./points/point');assert len(points)==2
        radii=[float(p.get('radius')) for p in points];assert radii[0]==radii[1]
        ws=[{bone.get('name'):float(bone.get('weight')) for bone in p.findall('./bones/bone')} for p in points]
        assert all(len(w)<=2 and abs(sum(w.values())-1)<1e-6 for w in ws)
        result.append(dict(name=cap.get('name'),endpoints_m=[a.tolist(),b.tolist()],radius_m=radii[0],bones=[next(iter(w)) for w in ws],endpoint_weights=ws))
    return result
