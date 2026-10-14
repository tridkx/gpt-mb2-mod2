"""Use one smooth height attachment coordinate for every overlapping sleeve layer."""
import numpy as np
def coherent_weights(p):
    def smooth(a,b,x):
        t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
    x=np.abs(p[:,0]);clavicle=1-smooth(.12,.19,x);proximal=smooth(1.10,1.45,p[:,2]);w=np.zeros((len(p),28))
    for sign,c,u,f in [(-1,14,15,17),(1,21,22,24)]:
        m=p[:,0]*sign>0;w[m,c]=proximal[m]*clavicle[m];w[m,u]=proximal[m]*(1-clavicle[m]);w[m,f]=1-proximal[m]
    return w
def apply(p,old,other_positions):
    weights=coherent_weights(p);shared={tuple(v) for v in np.round(other_positions,5)};contact=np.array([tuple(v) in shared for v in np.round(p,5)]);weights[contact]=old[contact];return weights,contact
