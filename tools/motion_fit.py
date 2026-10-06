"""Shoulder posture, torso volume and continuous skirt skinning in game coordinates."""
import numpy as np

ARM_FORWARD_DEGREES = 26.0
TORSO_WIDTH_SCALE = 1.08
TORSO_DEPTH_SCALE = 1.05
TORSO_CENTER_Y = .02

def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)

def forward_arms(positions, weights, joints):
    angle = np.radians(ARM_FORWARD_DEGREES)
    c, s = np.cos(angle), np.sin(angle)
    # +Y is forward. Rotating a descending arm around +X moves it forward.
    rotation = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    original = positions.copy()
    result = original.copy()
    for bones, shoulder in [(range(14,21),15), (range(21,28),22)]:
        influence = weights[:, list(bones)].sum(1)
        rotated = (original-joints[shoulder]) @ rotation.T + joints[shoulder]
        result += influence[:,None]*(rotated-original)
    return result

def torso_influence(source):
    height = smooth(.97,1.075,source[:,2])*(1-smooth(1.29,1.405,source[:,2]))
    central = 1-smooth(.14,.25,np.abs(source[:,0]))
    return height*central

def fuller_torso(positions, source):
    # Apply the same spatial field to exposed skin and every torso garment.
    # Fade out at the neck, shoulder tips and hips to keep their attachments.
    influence = torso_influence(source)
    result = positions.copy()
    result[:,0] += positions[:,0]*(TORSO_WIDTH_SCALE-1)*influence
    result[:,1] += (positions[:,1]-TORSO_CENTER_Y)*(TORSO_DEPTH_SCALE-1)*influence
    return result

def skirt_weights(source, core, front=1.0, back=.80, calf=1.0, waist_full=.86):
    amount = smooth(.99,waist_full,source[:,2])*(back+(front-back)*smooth(-.10,.03,source[:,1]))
    side = smooth(-.10,.10,source[:,0])
    knee = calf*smooth(.72,.32,source[:,2])
    result = core*(1-amount[:,None])
    for thigh, shin, fraction in [(1,2,1-side),(5,6,side)]:
        result[:,thigh] += amount*fraction*(1-knee)
        result[:,shin] += amount*fraction*knee
    # The engine accepts four influences. Normalize here, before seam merging.
    keep = np.argsort(-result,axis=1)[:,:4]
    mask = np.zeros_like(result); np.put_along_axis(mask,keep,1,1)
    result *= mask
    return result/np.maximum(result.sum(1,keepdims=True),1e-12)

def skirt_clearance(positions, source, lateral=.018, sagittal=.040):
    result = positions.copy()
    free = smooth(.94,.42,source[:,2])
    radial = result[:,:2]-[0,.02]
    radial /= np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1e-8)
    result[:,:2] += radial * free[:,None] * [lateral,sagittal]
    # Rear knee ease is local: it leaves the waist and hem silhouette unchanged.
    knee_t = np.clip((source[:,2]-.35)/(.88-.35),0,1)
    behind = 1-smooth(-.10,.01,source[:,1])
    result[:,1] -= .035*4*knee_t*(1-knee_t)*behind
    return result
