"""Local, shared deformation for Mingyu v1.0.1; native rig is preserved."""
import numpy as np
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def apply_proportions(points,settings,part,source_points):
    p=points.copy();d=np.zeros_like(p)
    head=smooth(1.48,1.57,p[:,2])
    pivot=np.array(settings['head_pivot'])
    d+=(p-pivot)*(settings['head_scale']-1)*head[:,None]
    neck=smooth(1.32,1.56,p[:,2])*(1-smooth(.10,.20,abs(p[:,0])))
    d[:,1]-=settings['neck_backward_m']*neck
    foot=1-smooth(.13,.25,p[:,2]) if part=='legs' else np.zeros(len(p))
    angle=np.radians(settings['foot_pitch_degrees']);c=np.cos(angle);s=np.sin(angle)
    rot=np.array([[1,0,0],[0,c,-s],[0,s,c]])
    ankle=np.array(settings['foot_pivot'])
    q=(p-ankle)@rot.T+ankle
    q[:,1]=ankle[1]+(q[:,1]-ankle[1])*settings['foot_length_scale']
    q[:,2]+=settings['foot_ground_shift_m']
    if part=='legs':
        sole=1-smooth(.0001,.012,source_points[:,2])
        q[:,2]+=(settings['sole_ground_m']-q[:,2])*sole
    d+=(q-p)*foot[:,None]
    return p+d
