"""One source-specific smooth fixed-to-hem policy for source and native proxy."""
import numpy as np
def smoothstep(a,b,x):
    t=np.clip((np.asarray(x)-a)/(b-a),0,1);return t*t*(3-2*t)
def travel(z,policy):
    z=np.asarray(z);fade=1-smoothstep(policy['transition_end_z_m'],policy['fixed_above_z_m'],z)
    return np.minimum(np.maximum(policy['fixed_above_z_m']-z,0)*policy['travel_slope']*fade,policy['max_travel_m'])
def reference_weights(p,policy):
    follow=policy['thigh_follow']*(1-smoothstep(.80,1.,p[:,2]));side=smoothstep(-.07,.07,p[:,0]);w=np.zeros((len(p),28));w[:,0]=1-follow;w[:,1]=follow*(1-side);w[:,5]=follow*side;return w
