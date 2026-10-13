"""Deterministic CPU PBD diagnostic, inspired by the installed cloth shader.

This is not the Bannerlord engine. No runtime binary or shader is distributed.
"""
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class Settings:
    fps: float = 60
    substeps: int = 2
    iterations: int = 3
    damping: float = .98  # velocity retained per substep, NOT engine material conversion
    stretch: float = .9
    shear: float = .8
    bend: float = .25
    anchor: float = .8
    gravity: float = 9.81
    thickness: float = .001
    penetration_tolerance: float = .002
    strain_tolerance: float = .25
    dummy_collision: bool = True

    def validate(self):
        if not all(np.isfinite(v) for v in asdict(self).values()):
            raise ValueError('nonfinite settings')
        if self.fps <= 0 or self.substeps < 1 or self.iterations < 1:
            raise ValueError('fps, substeps and iterations must be positive')
        for key in ('damping', 'stretch', 'shear', 'bend', 'anchor'):
            if not 0 <= getattr(self, key) <= 1:
                raise ValueError(key + ' must be in [0,1]')
        if min(self.gravity, self.thickness, self.penetration_tolerance, self.strain_tolerance) < 0:
            raise ValueError('negative gravity/thickness/tolerance')


def capsule_delta(points, capsule, thickness=0):
    """Closest-axis projection; varying radii are a tapered-capsule approximation."""
    a, b = capsule[:2, :3]
    axis = b-a
    t = np.clip((points-a) @ axis / max(float(axis@axis), 1e-15), 0, 1)
    d = points-a-t[:, None]*axis
    distance = np.linalg.norm(d, axis=1)
    radius = capsule[0, 3]*(1-t) + capsule[1, 3]*t + thickness
    depth = np.maximum(radius-distance, 0)
    # A point exactly on the axis still needs a finite outward direction.
    unit = d/np.maximum(distance[:, None], 1e-15)
    fallback = np.cross(axis, [1., 0, 0])
    if np.linalg.norm(fallback) < 1e-10:
        fallback = np.array([0., 1, 0])
    fallback /= np.linalg.norm(fallback)
    unit[distance < 1e-12] = fallback
    return unit*depth[:, None], depth


SAMPLES = np.array([[2/3, 1/6, 1/6], [1/6, 2/3, 1/6],
                    [1/6, 1/6, 2/3], [1/3, 1/3, 1/3]])


class Simulator:
    def __init__(self, data, triangles, settings):
        settings.validate()
        self.d = data
        self.tri = np.asarray(triangles, int).reshape(-1, 3)
        self.s = settings
        self.n = int(data['vertex_count'])
        self.active = np.asarray(data['max_distances']) > 0
        self.ids = np.flatnonzero(self.active)
        self.edges = np.asarray(data['constraints'], int)
        self.lengths = np.asarray(data['rest_lengths'], float)
        self.roots = (data['anchors'] >> 16).astype(int)
        self.anchor_lengths = (data['anchors'] & 65535)*data['anchor_scale']
        self.groups = []
        self.stretch_ids = []
        for row in data['constraint_sets']:
            for kind, (start, count) in enumerate(row.reshape(4, 2)):
                if count:
                    idx = np.arange(start, start+count)
                    self.groups.append((idx, (settings.stretch, settings.shear,
                                              settings.bend, 1.)[kind]))
                    if kind == 0:
                        self.stretch_ids.extend(idx)
        self.stretch_ids = np.array(self.stretch_ids, int)
        self.dummy_groups = [data['dummy_indices'].reshape(-1, 3)[start:start+count]
                             for count, start in data['dummy_sets']]

    def clamp(self, x, anchors, travel):
        delta = x-anchors
        distance = np.linalg.norm(delta, axis=1)
        x[:] = anchors + delta*np.minimum(1, travel/np.maximum(distance, 1e-15))[:, None]
        x[~self.active] = anchors[~self.active]

    def constraints(self, x):
        for idx, stiffness in self.groups:
            i, j = self.edges[idx].T
            wi, wj = self.active[i].astype(float), self.active[j].astype(float)
            delta = x[j]-x[i]
            distance = np.linalg.norm(delta, axis=1)
            correction = delta*((1-self.lengths[idx]/np.maximum(distance, 1e-15))
                                *stiffness/np.maximum(wi+wj, 1))[:, None]
            # Groups from payload must have no mutable write conflicts.
            x[i] += correction*wi[:, None]
            x[j] -= correction*wj[:, None]

    def collisions(self, x, capsules):
        for cap in capsules:
            delta, _ = capsule_delta(x[self.ids], cap, self.s.thickness)
            x[self.ids] += delta
        if not self.s.dummy_collision:
            return
        # Four interior samples per triangle; fixed vertices never projected.
        for triangles in self.dummy_groups:
            if not len(triangles):
                continue
            movable = self.active[triangles].astype(float)
            for weights in SAMPLES:
                q = np.einsum('tvc,v->tc', x[triangles], weights)
                projected = q.copy()
                for cap in capsules:
                    delta, _ = capsule_delta(projected, cap, self.s.thickness)
                    projected += delta
                denom = (movable*weights**2).sum(1)
                correction = (projected-q)/np.maximum(denom[:, None], 1e-15)
                for k in range(3):
                    x[triangles[:, k]] += correction*(movable[:, k]*weights[k])[:, None]

    def metrics(self, x, anchors, capsules, travel):
        vertex_depth = np.zeros(len(self.ids))
        # Metrics also sample fixed surfaces: collision projection cannot fix them.
        fixed_depth = np.zeros(int((~self.active).sum()))
        triangles = self.tri[np.any(self.active[self.tri], axis=1)]
        q = np.einsum('tvc,sv->tsc', x[triangles], SAMPLES).reshape(-1, 3)
        surface_depth = np.zeros(len(q))
        for cap in capsules:
            vertex_depth = np.maximum(vertex_depth, capsule_delta(x[self.ids], cap)[1])
            fixed_depth = np.maximum(fixed_depth, capsule_delta(x[~self.active], cap)[1])
            surface_depth = np.maximum(surface_depth, capsule_delta(q, cap)[1])
        travel_error = np.maximum(np.linalg.norm(x-anchors, axis=1)-travel, 0)
        idx = self.stretch_ids
        current = np.linalg.norm(x[self.edges[idx, 0]]-x[self.edges[idx, 1]], axis=1)
        strain = np.abs(current/np.maximum(self.lengths[idx], 1e-15)-1)
        row = dict(vertex_penetration_m=float(vertex_depth.max(initial=0)),
                   interior_penetration_m=float(surface_depth.max(initial=0)),
                   fixed_penetration_m=float(fixed_depth.max(initial=0)),
                   max_stretch_strain=float(strain.max(initial=0)),
                   max_stretch_error_m=float(np.abs(current-self.lengths[idx]).max(initial=0)),
                   p99_stretch_strain=float(np.percentile(strain, 99)) if len(strain) else 0.,
                   travel_exceeded_m=float(travel_error.max(initial=0)),
                   fixed_drift_m=float(np.linalg.norm((x-anchors)[~self.active], axis=1).max(initial=0)),
                   max_displacement_m=float(np.linalg.norm(x-anchors, axis=1).max(initial=0)))
        heat = np.zeros(self.n)
        heat[self.ids] = vertex_depth
        return row, heat

    def run(self, anchors, capsules, travel):
        anchors = np.asarray(anchors, float)
        capsules = np.asarray(capsules, float)
        travel = np.asarray(travel, float)
        if anchors.ndim != 3 or anchors.shape[1:] != (self.n, 3) or not len(anchors):
            raise ValueError('anchors must have shape (frames, simulation vertices, 3)')
        if capsules.ndim != 4 or capsules.shape[0] != len(anchors) or capsules.shape[2:] != (2, 4):
            raise ValueError('capsules must have shape (frames, count, 2, xyz+radius)')
        if travel.shape != (self.n,) or (travel < 0).any():
            raise ValueError('invalid travel')
        if not all(np.isfinite(a).all() for a in (anchors, capsules, travel)):
            raise ValueError('nonfinite motion input')
        if (capsules[..., 3] < 0).any():
            raise ValueError('negative capsule radii')
        x = anchors[0].copy()
        velocity = np.zeros_like(x)
        positions, rows, heats = [], [], []
        dt = 1/(self.s.fps*self.s.substeps)
        acceleration = np.array([0, 0, -self.s.gravity])
        for frame in range(len(anchors)):
            if frame:
                for step in range(self.s.substeps):
                    blend = (step+1)/self.s.substeps
                    center = anchors[frame-1]*(1-blend)+anchors[frame]*blend
                    caps = capsules[frame-1]*(1-blend)+capsules[frame]*blend
                    old = x.copy()
                    x[self.ids] += velocity[self.ids]*dt*self.s.damping + acceleration*dt*dt
                    self.clamp(x, center, travel)
                    for _ in range(self.s.iterations):
                        delta = x-x[self.roots]
                        distance = np.linalg.norm(delta, axis=1)
                        correction = np.maximum(distance-self.anchor_lengths, 0)
                        x[self.ids] -= (delta/np.maximum(distance[:, None], 1e-15)
                                        *correction[:, None]*self.s.anchor)[self.ids]
                        self.constraints(x)
                        self.collisions(x, caps)
                        # Deliberate difference from shader: enforce hard travel and pins last.
                        # Any unsatisfiable collision is preserved as residual in metrics.
                        self.clamp(x, center, travel)
                    velocity = (x-old)/dt
                    velocity[~self.active] = 0
                    if not np.isfinite(x).all():
                        raise FloatingPointError(f'nonfinite positions at frame {frame}')
            row, heat = self.metrics(x, anchors[frame], capsules[frame], travel)
            row['frame'] = frame
            row['time_s'] = frame/self.s.fps
            rows.append(row)
            positions.append(x.astype(np.float32).copy())
            heats.append(heat.astype(np.float32))
        return np.array(positions), rows, np.array(heats)
