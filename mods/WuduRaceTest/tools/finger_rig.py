"""Measured finger chains, shared by Blender construction and offline posing."""
import numpy as np

# Right hand coordinates in its existing rest frame, metres at final scale.
# Each row is MCP, PIP, DIP and fingertip; thumb uses CMC, MCP and IP.
CHAINS = {
    'thumb': [[.005, .000, .019], [.019, .007, .028], [.031, .009, .038], [.042, .010, .044]],
    'index': [[.045, .001, .020], [.065, .008, .024], [.079, .012, .026], [.094, .013, .028]],
    'middle': [[.046, -.003, .003], [.073, .002, .007], [.089, .006, .009], [.106, .007, .011]],
    'ring': [[.043, -.010, -.013], [.068, -.006, -.009], [.085, -.002, -.007], [.100, .001, -.005]],
    'little': [[.038, -.016, -.028], [.059, -.014, -.028], [.073, -.009, -.027], [.087, -.007, -.025]],
}
ANGLES = np.radians([48., 62., 42.])

def extend(world, parents, names):
    worlds = list(world.copy()); parents = list(parents); names = list(names)
    rows = []; segments = {}
    for side, sign, hand in [('l', -1, 19), ('r', 1, 26)]:
        # Mirror geometry, then rebuild a right-handed joint basis.
        mirror = np.diag([sign, 1, 1])
        right = world[26]
        normal = mirror @ right[:3, 1]
        for finger, points in CHAINS.items():
            p = (np.array(points) @ right[:3, :3].T + right[:3, 3]) @ mirror
            ids = []
            for j in range(3):
                direction = p[j+1] - p[j]; direction /= np.linalg.norm(direction)
                axis = np.cross(direction, normal); axis /= np.linalg.norm(axis)
                z = np.cross(axis, direction)
                frame = np.eye(4); frame[:3, :3] = np.column_stack([axis, direction, z]); frame[:3, 3] = p[j]
                index = len(worlds); parent = hand if j == 0 else index-1
                worlds.append(frame); parents.append(parent); names.append(f'{side}_{finger}_{j+1}')
                ids.append(index)
                rows.append(dict(index=index, name=names[-1], parent=parent, head=p[j].tolist(), tail=p[j+1].tolist()))
            segments[(sign, finger)] = (p, ids)
    return np.array(worlds), np.array(parents), names, rows, segments

def skin_weights(points, old_weights, segments):
    w = np.pad(old_weights, ((0, 0), (0, 30)))
    for sign, hand in [(-1, 19), (1, 26)]:
        ix = np.where(points[:, 0]*sign > 0)[0]; p = points[ix]
        candidates = []
        for finger in CHAINS:
            chain, ids = segments[(sign, finger)]
            delta = chain[1:] - chain[:-1]; lengths = np.linalg.norm(delta, axis=1)
            t = np.clip(np.sum((p[:, None]-chain[:-1])*delta, axis=2)/(lengths**2), 0, 1)
            distances = np.linalg.norm(p[:, None]-chain[:-1]-t[:, :, None]*delta, axis=2)
            seg = np.argmin(distances, axis=1)
            candidates.append((distances.min(axis=1), chain, ids, seg, t, lengths))
        distances=np.array([x[0] for x in candidates]).T
        branch_weights=np.exp(-(distances-distances.min(axis=1,keepdims=True))/.004)
        branch_weights/=branch_weights.sum(axis=1,keepdims=True)
        addition=np.zeros((len(ix),58));total=np.zeros(len(ix))
        for branch, (_, chain, ids, seg, t, lengths) in enumerate(candidates):
            select = np.arange(len(ix))
            if not len(select): continue
            # Root blend uses the signed proximal distance, so the palm stays fixed.
            direction = (chain[1]-chain[0])/lengths[0]
            axial = (p[select]-chain[0])@direction
            blend = np.clip(axial/.016, 0, 1); blend = blend*blend*(3-2*blend)
            if branch==0:
                # Thumb's oblique chain must not pull the centre of the palm.
                normal=chain[3]-chain[0]
                lateral=(p[select]-chain[0])@normal/np.linalg.norm(normal)
                gate=np.clip(lateral/.022,0,1);blend*=gate*gate*(3-2*gate)
            blend*=branch_weights[select,branch]
            arc = np.cumsum(np.r_[0, lengths]); s = seg[select]
            distance = arc[s]+t[select, s]*lengths[s]
            # Interpolate between joint influences around PIP and DIP.
            joint = np.zeros((len(select), 3))
            a = np.clip((distance-(arc[1]-.005))/.010, 0, 1)
            b = np.clip((distance-(arc[2]-.004))/.008, 0, 1)
            joint[:, 0] = 1-a; joint[:, 1] = a*(1-b); joint[:, 2] = b
            total[select]+=blend
            addition[np.ix_(select, ids)] += joint*blend[:, None]
        w[ix]=w[ix]*(1-total[:,None])+addition
    mask = np.zeros_like(w); np.put_along_axis(mask, np.argsort(-w, axis=1)[:, :4], 1, 1)
    w *= mask
    return w/w.sum(axis=1, keepdims=True)

def pose_world(rig, left=0., right=0., native_world=None):
    world = rig['restWorld'].copy() if native_world is None else native_world.copy()
    for i in range(28, len(world)):
        local = rig['restLocal'][i].copy()
        value = left if i < 43 else right
        angle = ANGLES[(i-28)%3]*value
        c, s = np.cos(angle), np.sin(angle)
        local[:3, :3] = local[:3, :3] @ np.array([[1,0,0],[0,c,-s],[0,s,c]])
        world[i] = world[rig['parent'][i]] @ local
    return world
