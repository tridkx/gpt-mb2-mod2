"""Native animation reconstruction for offline sleeve checks; no engine IK/physics."""
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def rest_matrices(raw):
    local=np.array([np.array(b['rest']).reshape(4,4).T for b in raw['bones']])
    local[:,3,:]=[0,0,0,1]
    world=local.copy()
    for i,b in enumerate(raw['bones']):
        if b['parent']>=0:world[i]=world[b['parent']]@local[i]
    return local,world

def skin_frames(raw,anim):
    local,bind=rest_matrices(raw)
    duration=int(anim['duration'])
    tracks=anim['boneAnims']
    assert len(tracks)==len(raw['bones']) and all(t['rot'] for t in tracks)
    frames=np.arange(1,duration,dtype=float)
    result=np.repeat(local[None],len(frames),axis=0)
    for track in tracks:
        i=track['i']; keys=track['rot']; times=np.array([k['t'] for k in keys])
        rotations=Rotation.from_quat([k['q'] for k in keys])
        result[:,i,:3,:3]=Slerp(times,rotations)(np.clip(frames,times[0],times[-1])).as_matrix() if len(keys)>1 else rotations.as_matrix()[0]
    root=anim.get('rootPosition',[])
    if root:
        times=np.array([k['t'] for k in root]); values=np.array([k['v'][:3] for k in root])
        result[:,0,:3,3]+=np.column_stack([np.interp(frames,times,values[:,j]) for j in range(3)])
    for i,b in enumerate(raw['bones']):
        if b['parent']>=0:result[:,i]=result[:,b['parent']]@result[:,i]
    return result@np.linalg.inv(bind),result

def posed(mesh,skin):
    p=np.array(mesh['pos']);bi=np.array(mesh['bi']);bw=np.array(mesh['bw'])/255.0
    h=np.column_stack([p,np.ones(len(p))]);out=np.zeros_like(p)
    for j in range(4):out+=bw[:,j,None]*np.einsum('nij,nj->ni',skin[bi[:,j]],h)[:,:3]
    return out
