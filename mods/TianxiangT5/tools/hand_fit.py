"""Keep native grip anchors while separating forearm twist from palm skinning."""
import numpy as np


def smooth(a, b, value):
    t = np.clip((value-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def forearm_coordinate(positions, elbow, wrist):
    axis = wrist-elbow
    t = (positions-elbow) @ axis / (axis @ axis)
    distance = np.linalg.norm(positions-elbow-t[:, None]*axis, axis=1)
    return t, distance


def forearm_weights(positions, original_weights, source_joints):
    result = original_weights.copy()
    changed = np.zeros(len(positions),bool)
    for elbow, twist, wrist, sign in [(17,18,19,-1), (24,25,26,1)]:
        t, distance = forearm_coordinate(positions, source_joints[elbow], source_joints[wrist])
        region = (positions[:,0]*sign > .27) & (distance < .14) & (positions[:,2] > .88)
        influence = smooth(-.05,.15,t)*region
        changed |= influence > 0
        fore = smooth(.15,.80,t)
        hand = smooth(.83,1.01,t)
        corrected = np.zeros_like(result)
        corrected[:,elbow] = 1-fore
        corrected[:,twist] = fore*(1-hand)
        corrected[:,wrist] = fore*hand
        result = result*(1-influence[:,None])+corrected*influence[:,None]
    # At most four influences; the palm is rigid to its actual native hand bone.
    corrected = result[changed]
    keep = np.argsort(-corrected,axis=1)[:,:4]
    mask = np.zeros_like(corrected)
    np.put_along_axis(mask,keep,1,1)
    corrected *= mask
    result[changed] = corrected/np.maximum(corrected.sum(1,keepdims=True),1e-12)
    return result


def posture_fade(positions, source_joints, elbow, wrist):
    t, _ = forearm_coordinate(positions, source_joints[elbow], source_joints[wrist])
    # Keep the shoulder/upper arm setting, but end all mesh displacement before
    # the wrist. Weapons attach to the unmodified native skeleton, not this mesh.
    return 1-smooth(-.02,.98,t)
