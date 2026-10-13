"""Behavior checks: gravity, moving pins, collision conflicts and interior sampling."""
import unittest
import tempfile
from pathlib import Path
import numpy as np
from solver import Settings, Simulator, capsule_delta


def fixture():
    rest = np.array([[-.2, 0, 1], [.2, 0, 1], [-.2, 0, .5], [.2, 0, .5]])
    edges = np.array([[0, 2], [1, 3], [2, 3]])
    data = dict(vertex_count=4, max_distances=np.array([0., 0, .5, .5]),
                constraints=edges, rest_lengths=np.linalg.norm(rest[edges[:, 0]]-rest[edges[:, 1]], axis=1),
                anchors=np.array([0, 1<<16, 32768, (1<<16)|32768], np.uint32), anchor_scale=.5/32768,
                constraint_sets=np.array([[0, 2, 2, 0, 2, 0, 2, 0], [2, 1, 3, 0, 3, 0, 3, 0]]),
                dummy_indices=np.array([0, 2, 3, 0, 3, 1]), dummy_sets=np.array([[1, 0], [1, 1]]))
    return rest, data, np.array([[0, 2, 3], [0, 3, 1]])


class SolverChecks(unittest.TestCase):
    def test_gravity_and_moving_pins(self):
        rest, data, tri = fixture()
        anchors = np.repeat(rest[None], 12, axis=0)
        anchors[:, :, 0] += np.linspace(0, .05, 12)[:, None]
        caps = np.empty((12, 0, 2, 4))
        s = Settings(stretch=0, bend=0, anchor=0, dummy_collision=False)
        positions, rows, _ = Simulator(data, tri, s).run(anchors, caps, data['max_distances'])
        self.assertLess(positions[-1, 2, 2], anchors[-1, 2, 2]-.01)
        np.testing.assert_allclose(positions[:, :2], anchors[:, :2], atol=1e-7)
        self.assertLess(max(r['travel_exceeded_m'] for r in rows), 1e-10)
        np.testing.assert_array_equal(positions, Simulator(data, tri, s).run(anchors, caps, data['max_distances'])[0])

    def test_stiffness_reduces_stretch(self):
        rest, data, tri = fixture()
        anchors = np.repeat(rest[None], 20, axis=0)
        caps = np.empty((20, 0, 2, 4))
        def strain(stiffness):
            _, rows, _ = Simulator(data, tri, Settings(stretch=stiffness, anchor=0)).run(anchors, caps, data['max_distances'])
            return rows[-1]['max_stretch_strain']
        self.assertLess(strain(.9), strain(0)/10)

    def test_axis_point_is_projected(self):
        cap = np.array([[0, 0, 0, .2], [0, 0, 1, .2]])
        delta, depth = capsule_delta(np.array([[0., 0, .5]]), cap)
        self.assertAlmostEqual(np.linalg.norm(delta), .2)
        self.assertAlmostEqual(depth[0], .2)

    def test_impossible_collision_is_reported(self):
        rest, data, tri = fixture()
        data['max_distances'][2:] = .001
        anchors = np.repeat(rest[None], 5, axis=0)
        cap = np.array([[-.2, 0, .4, .1], [-.2, 0, .6, .1]])
        caps = np.repeat(cap[None, None], 5, axis=0)
        positions, rows, _ = Simulator(data, tri, Settings()).run(anchors, caps, data['max_distances'])
        self.assertGreater(rows[-1]['vertex_penetration_m'], .09)
        self.assertLess(rows[-1]['travel_exceeded_m'], 1e-10)
        np.testing.assert_allclose(positions[:, :2], anchors[:, :2], atol=1e-7)

    def test_triangle_interior_detected_with_clear_vertices(self):
        rest, data, tri = fixture()
        center = rest[tri[0]].mean(0)
        cap = np.array([np.r_[center, .04], np.r_[center, .04]])[None]
        row, _ = Simulator(data, tri, Settings()).metrics(rest, rest, cap, data['max_distances'])
        self.assertEqual(row['vertex_penetration_m'], 0)
        self.assertGreater(row['interior_penetration_m'], .039)

    def test_invalid_input_rejected(self):
        rest, data, tri = fixture()
        anchors = np.repeat(rest[None], 2, axis=0)
        anchors[0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            Simulator(data, tri, Settings()).run(anchors, np.empty((2, 0, 2, 4)), data['max_distances'])
        with self.assertRaises(ValueError):
            Settings(damping=2).validate()

    def test_capsule_frame_and_bone_transform(self):
        from run import capsule_tracks
        xml = '''<bodies><body name="test"><capsules><capsule length=".5" frame="0,0,-1,0,0,1,0,0,1,0,0,0,.2,0,1,1"><points>
        <point radius=".1"><bones><bone name="root" weight="1"/></bones></point>
        <point radius=".1"><bones><bone name="root" weight="1"/></bones></point>
        </points></capsule></capsules></body></bodies>'''
        matrices = np.eye(4)[None, None].copy()
        matrices[0, 0, 0, 3] = .1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'caps.xml'
            path.write_text(xml)
            caps, tapered = capsule_tracks(path, 'test', dict(names=['root']), matrices)
        np.testing.assert_allclose(caps[0, 0, :, :3], [[.3, 0, 1], [.3, 0, .5]])
        self.assertFalse(tapered)

    def test_unknown_collision_bone_rejected(self):
        from run import capsule_tracks
        xml = '''<bodies><body name="test"><capsules><capsule length="1" frame="1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1"><points>
        <point radius=".1"><bones><bone name="missing" weight="1"/></bones></point>
        <point radius=".1"><bones><bone name="missing" weight="1"/></bones></point>
        </points></capsule></capsules></body></bodies>'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'caps.xml'
            path.write_text(xml)
            with self.assertRaises(ValueError):
                capsule_tracks(path, 'test', dict(names=['root']), np.eye(4)[None, None])


if __name__ == '__main__':
    unittest.main()
