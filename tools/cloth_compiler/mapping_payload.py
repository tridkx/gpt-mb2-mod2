"""Native af41613e mapping: ushort triangle indices and float4 barycentric offsets.

Validated against installed armor and awning samples; no game solver is emulated.
"""
import struct
import numpy as np

def read(raw):
    n=struct.unpack_from('<I',raw)[0];offset=4+n*2
    indices=np.frombuffer(raw,'<u2',n,4).copy().reshape(-1,3)
    m=struct.unpack_from('<I',raw,offset)[0]
    weights=np.frombuffer(raw,'<f4',m,offset+4).copy().reshape(-1,4)
    assert len(indices)==len(weights) and offset+4+m*4==len(raw)
    return indices,weights

def write(indices,weights):
    indices=np.asarray(indices,'<u2');weights=np.asarray(weights,'<f4')
    assert indices.shape==(len(weights),3) and weights.shape[1]==4
    return struct.pack('<I',indices.size)+indices.tobytes()+struct.pack('<I',weights.size)+weights.tobytes()

def reconstruct(points,normals,indices,weights):
    bary=weights[:,:3];p=(points[indices]*bary[:,:,None]).sum(1)
    n=(normals[indices]*bary[:,:,None]).sum(1);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
    return p+n*weights[:,3,None]

def project(points,vertices,normals,triangles):
    """Solve the shader's barycentric-plus-interpolated-normal reconstruction."""
    from scipy.spatial import cKDTree
    tri=vertices[triangles];centers=tri.mean(1);tree=cKDTree(centers)
    _,candidate=tree.query(points,k=min(16,len(tri)))
    if candidate.ndim==1:candidate=candidate[:,None]
    corners=tri[candidate];tn=normals[triangles[candidate]]
    e1=corners[:,:,1]-corners[:,:,0];e2=corners[:,:,2]-corners[:,:,0]
    normal=np.cross(e1,e2);normal/=np.maximum(np.linalg.norm(normal,axis=2)[:,:,None],1e-12)
    q=points[:,None]-corners[:,:,0]
    coeff=np.linalg.solve(np.stack([e1,e2,normal],axis=-1),q[...,None])[...,0]
    for _ in range(25):
        bary=np.stack([1-coeff[:,:,0]-coeff[:,:,1],coeff[:,:,0],coeff[:,:,1]],axis=-1)
        raw_normal=(tn*bary[:,:,:,None]).sum(2);size=np.maximum(np.linalg.norm(raw_normal,axis=2),1e-12)
        normal=raw_normal/size[:,:,None]
        da=tn[:,:,1]-tn[:,:,0];db=tn[:,:,2]-tn[:,:,0]
        dna=(da-normal*(normal*da).sum(2)[:,:,None])/size[:,:,None]
        dnb=(db-normal*(normal*db).sum(2)[:,:,None])/size[:,:,None]
        residual=q-e1*coeff[:,:,0,None]-e2*coeff[:,:,1,None]-normal*coeff[:,:,2,None]
        jacobian=np.stack([e1+dna*coeff[:,:,2,None],e2+dnb*coeff[:,:,2,None],normal],axis=-1)
        step=np.linalg.solve(jacobian,residual[...,None])[...,0]
        coeff+=step*np.minimum(1,.5/np.maximum(abs(step[:,:,:2]).max(2),1e-12))[:,:,None]
    bary=np.stack([1-coeff[:,:,0]-coeff[:,:,1],coeff[:,:,0],coeff[:,:,1]],axis=-1)
    normal=(tn*bary[:,:,:,None]).sum(2);normal/=np.maximum(np.linalg.norm(normal,axis=2)[:,:,None],1e-12)
    rebuilt=(corners*bary[:,:,:,None]).sum(2)+normal*coeff[:,:,2,None]
    error=np.linalg.norm(rebuilt-points[:,None],axis=2)
    penalty=np.maximum(-bary,0).sum(2)+np.maximum(bary-1,0).sum(2)
    cost=np.abs(coeff[:,:,2])+penalty*.25+error*100
    choice=cost.argmin(1);row=np.arange(len(points))
    indices=triangles[candidate[row,choice]]
    weights=np.column_stack([bary[row,choice],coeff[row,choice,2]]).astype('f4')
    assert np.isfinite(weights).all()
    return indices,weights
