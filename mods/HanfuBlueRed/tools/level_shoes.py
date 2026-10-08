from pathlib import Path
"""Level the model-specific soles in native standing frame 1, preserving seams."""
import json,sys
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices

def level(objects,records,arrays,root):
    rig=parse_skeljson(json.loads((root/'reports/human_skeleton.json').read_text()))
    animation=parse_animjson(json.loads((root/'reports/idle.json').read_text()))
    skin=skin_matrices(rig,animation,1)
    target=rig['restWorld'][:,:3,3]
    corrections={};report=[]
    for sign,bone,toe_bone in [(-1,3,4),(1,7,8)]:
        p=np.concatenate([arrays[r['object']]['P'] for r in records if r['kind']=='shoe' and np.mean(arrays[r['object']]['P'][:,0])*sign>0])
        f=target[toe_bone]-target[bone];f[2]=0;f/=np.linalg.norm(f)
        forward=p@f;lo,hi=forward.min(),forward.max()
        heel=forward<lo+(hi-lo)*.25;toe=forward>lo+(hi-lo)*.75
        axis=np.array([f[1],-f[0],0]);pivot=target[bone]
        k=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
        def rotate(angle):return np.eye(3)+np.sin(angle)*k+(1-np.cos(angle))*(k@k)
        def pose(q):return q@skin[bone,:3,:3].T+skin[bone,:3,3]
        def candidate(angle):return (p-pivot)@rotate(angle).T+pivot
        def gap(angle):
            q=pose(candidate(angle));return float(q[heel,2].min()-q[toe,2].min())
        before=pose(p);a,b=-.15,.65
        assert gap(a)>0 and gap(b)<0
        for _ in range(55):
            mid=(a+b)/2
            if gap(mid)>0:a=mid
            else:b=mid
        angle=(a+b)/2;rot=rotate(angle);q=pose(candidate(angle))
        # Translate along posed world vertical to place the lowest sole point
        # on z=0, then convert this correction back into the bind coordinates.
        floor=float(q[:,2].min());shift=skin[bone,:3,:3].T@np.array([0,0,-floor])
        after=pose(candidate(angle)+shift)
        corrections[sign]=(rot,pivot,shift)
        report.append({'bone':bone,'side':'left' if sign<0 else 'right','rotation_degrees':float(np.degrees(angle)),
                       'bind_translation':shift.tolist(),'before_heel_toe_gap':float(before[heel,2].min()-before[toe,2].min()),
                       'after_heel_toe_gap':float(after[heel,2].min()-after[toe,2].min()),'after_lowest_sole':float(after[:,2].min()),
                       'after_heel_height':float(after[heel,2].min()),'after_toe_height':float(after[toe,2].min())})
    for o,r in zip(objects,records):
        if r['part']!='legs':continue
        a=arrays[o.name];p=a['P'].copy();result=p.copy()
        for sign,(rot,pivot,shift) in corrections.items():
            ids=np.where(p[:,0]*sign>=0)[0]
            weight=np.ones(len(ids))
            if r['kind']=='pants':
                t=np.clip((p[ids,2]-.14)/(.30-.14),0,1);weight=1-t*t*(3-2*t)
            corrected=(p[ids]-pivot)@rot.T+pivot+shift
            result[ids]=p[ids]+weight[:,None]*(corrected-p[ids])
        a['P']=result
        for v,co in zip(o.data.vertices,result):v.co=co
        r['bounds']=[result.min(0).tolist(),result.max(0).tolist()]
    return {'reference_animation':'anim_inventory_idle','reference_frame':1,'floor_z':0,'sides':report,
            'pants_transition_z':[.14,.30],'bone_weights_changed':False,'game_test_verified':False}
