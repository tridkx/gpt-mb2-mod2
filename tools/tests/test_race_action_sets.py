import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from race_action_sets import complete, validate


class ActionSetTests(unittest.TestCase):
    def setUp(self):
        self.native = ET.fromstring('''<action_sets>
          <action_set id="as_human_warrior" skeleton="human"><action type="idle" animation="native"/></action_set>
          <action_set id="as_human_female_warrior" skeleton="human" base_set="as_human_warrior"/>
          <action_set id="as_human_map" skeleton="human" base_set="as_human_warrior"/>
          <action_set id="as_human_poses" skeleton="human" base_set="as_human_warrior"/>
        </action_sets>''')
        self.current = ET.fromstring('''<action_sets>
          <action_set id="as_short_warrior" skeleton="custom" base_set="as_human_warrior">
            <action type="idle" animation="chosen"/></action_set>
        </action_sets>''')

    def test_names_idle_preservation_female_poses_and_idempotence(self):
        original = ET.tostring(self.current[0])
        complete(self.native, self.current, 'long_race', 'custom', 'short')
        report = validate(self.native, self.current, 'long_race', 'custom', 'short')
        self.assertEqual(report['canonical_count'], 5)
        self.assertEqual(report['female_poses_base'], 'as_human_poses')
        self.assertEqual(ET.tostring(self.current[0]), original)
        self.assertEqual(self.current.find("action_set[@id='as_long_race_warrior']/action").get('animation'), 'chosen')
        once = ET.tostring(self.current)
        complete(self.native, self.current, 'long_race', 'custom', 'short')
        self.assertEqual(ET.tostring(self.current), once)

    def test_incomplete_registration_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing generated'):
            validate(self.native, self.current, 'long_race', 'custom', 'short')

    def test_wrong_skeleton_not_overwritten(self):
        ET.SubElement(self.current, 'action_set', id='as_long_race_map', skeleton='other')
        with self.assertRaisesRegex(ValueError, 'another skeleton'):
            complete(self.native, self.current, 'long_race', 'custom', 'short')

    def test_cycle_and_missing_base_rejected(self):
        complete(self.native, self.current, 'long_race', 'custom', 'short')
        node = self.current.find("action_set[@id='as_long_race_map']")
        node.set('base_set', 'as_long_race_map')
        with self.assertRaisesRegex(ValueError, 'cycle'):
            validate(self.native, self.current, 'long_race', 'custom', 'short')
        node.set('base_set', 'missing')
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            validate(self.native, self.current, 'long_race', 'custom', 'short')

    def test_duplicate_id_rejected(self):
        self.current.append(ET.fromstring(ET.tostring(self.current[0])))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            complete(self.native, self.current, 'long_race', 'custom', 'short')


if __name__ == '__main__':
    unittest.main()
