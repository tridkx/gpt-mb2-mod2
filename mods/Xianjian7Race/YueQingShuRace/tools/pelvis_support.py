"""Source-specific surface sampling and capsule clearance for pelvis support."""
import numpy as np

def pose_capsule(cap,skin,names):
    endpoints=[]
    for i,(point,bone) in enumerate(zip(cap['endpoints_m'],cap['bones'])):
        influences=cap.get('endpoint_weights',[[dict(bone=b,weight=1.)] for b in cap['bones']])[i]
        q=np.zeros(3)
        for influence in influences:
            m=skin[names.index(influence['bone'])]
            q+=influence['weight']*(m[:3,:3]@point+m[:3,3])
        endpoints.append(q)
    return np.array(endpoints)

def surface_samples(positions,faces,subdivisions=4):
    tri=positions[faces]
    keep=(tri[:,:,2].max(1)>.82)&(tri[:,:,2].min(1)<1.12)&(np.abs(tri[:,:,0]).min(1)<.20)
    tri=tri[keep];points=[]
    for i in range(subdivisions+1):
        for j in range(subdivisions+1-i):
            a=i/subdivisions;b=j/subdivisions
            points.append(tri[:,0]*a+tri[:,1]*b+tri[:,2]*(1-a-b))
    q=np.concatenate(points)
    return q[(np.abs(q[:,0])<.20)&(q[:,2]>.82)&(q[:,2]<1.12)]

def clearance(points,capsules):
    d=np.full(len(points),100.)
    for cap in capsules:
        a,b=np.array(cap['endpoints_m']);axis=b-a;t=np.clip((points-a)@axis/(axis@axis),0,1)
        d=np.minimum(d,np.linalg.norm(points-a-t[:,None]*axis,axis=1)-cap['radius_m'])
    return d
