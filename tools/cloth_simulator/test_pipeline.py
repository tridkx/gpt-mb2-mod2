"""Pipeline integration checks using a temporary mod and real CPU simulations.

Only TPAC extraction is substituted with the procedural final-data fixture.
No actual mod files, installed modules, game process or release archive is changed.
"""
from pathlib import Path
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import numpy as np

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
from cloth_simulator.pipeline import run_pipeline, ensure_diagnostics, sha, project_file
from cloth_compiler.cook_cloth import cook
import package_delivery


class PipelineChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.root = self.workspace/'mods/DemoCloth'
        for relative in ('reports', 'build/probe', 'module/DemoCloth/AssetPackages', 'module/DemoCloth/ModuleData'):
            (self.root/relative).mkdir(parents=True, exist_ok=True)
        (self.root/'README.md').write_text('Procedural test fixture')
        self.package = self.root/'module/DemoCloth/AssetPackages/test.tpac'
        self.package.write_bytes(b'procedural fake TPAC; extraction mocked, simulation real')
        (self.root/'module/DemoCloth/SubModule.xml').write_text('<Module><Id value="DemoCloth"/><Version value="v0.1.0"/></Module>')
        (self.root/'build/probe/NativeClothProbe.dll').write_bytes(b'fixture')
        skeleton = dict(bones=[dict(i=0, name='root', parent=-1, rest=np.eye(4).ravel().tolist())])
        self.write('reports/skeleton.json', skeleton)
        animation = dict(name='fixture_idle', boneNum=1, boneAnims=[dict(i=0,
            rot=[dict(t=f, q=[0, 0, 0, 1]) for f in range(5)])])
        self.write('reports/idle.json', animation)
        self.collision_x = 3.
        self.write_capsule()
        self.mesh = dict(name='fixture_cloth', guid='00000000-0000-0000-0000-000000000001',
            metamesh='fixture_body', lod=0, positions=[[-.2,0,1],[.2,0,1],[-.2,0,.5],[.2,0,.5]],
            normals=[[0,-1,0]]*4, alpha=[0,0,100,100], weights=[[255,0,0,0]]*4,
            bones=[[0,0,0,0]]*4, indices=[0,2,3,0,3,1])
        self.payload = cook(self.mesh)[0]
        self.mapped = False
        self.extraction_count = 0
        self.multiplier = 1.
        self.config = dict(id='DemoCloth', source_files=['README.md'], package='module/DemoCloth/AssetPackages/test.tpac',
            cloth_diagnostics=dict(enabled=True, mode='report', probe='build/probe/NativeClothProbe.dll', targets=[
                dict(metamesh='fixture_body', skeleton='reports/skeleton.json',
                     capsules='module/DemoCloth/ModuleData/capsules.xml', body='fixture_capsules', lods=[0],
                     meshes=['fixture_cloth'], settings=dict(warmup=2, substeps=1, iterations=1),
                     motions=[dict(name='idle', path='reports/idle.json', fps=60)])]))
        self.save_config()
        self.extract_patch = patch('cloth_simulator.run.extract', side_effect=self.extract)
        self.extract_patch.start()
        self.output = io.StringIO()
        self.quiet = contextlib.redirect_stdout(self.output)
        self.quiet.__enter__()

    def tearDown(self):
        self.quiet.__exit__(None, None, None)
        self.extract_patch.stop()
        self.temp.cleanup()

    def write(self, relative, value):
        (self.root/relative).write_text(json.dumps(value), encoding='utf-8')

    def save_config(self):
        self.write('mod.json', self.config)

    def write_capsule(self):
        xml = f'''<bodies><body name="fixture_capsules"><capsules><capsule length=".2" frame="0,0,1,0,0,1,0,0,-1,0,0,0,{self.collision_x},0,.4,1"><points>
        <point radius=".1"><bones><bone name="root" weight="1"/></bones></point>
        <point radius=".1"><bones><bone name="root" weight="1"/></bones></point>
        </points></capsule></capsules></body></bodies>'''
        (self.root/'module/DemoCloth/ModuleData/capsules.xml').write_text(xml)

    def extract(self, args):
        self.extraction_count += 1
        dest = args.output
        dest.mkdir(parents=True)
        stem = self.mesh['metamesh']+'_'+self.mesh['guid']
        (dest/(stem+'.bin')).write_bytes(self.payload)
        (dest/(stem+'.mesh.json')).write_text(json.dumps(self.mesh))
        self.metadata = dict(Name='fixture_body', ClothMetamesh='mapped_reference' if self.mapped else '00000000-0000-0000-0000-000000000000',
            meshes=[dict(Guid=self.mesh['guid'], Name=self.mesh['name'], UnknownFloat1=self.multiplier, ClothingMaterial={})])
        files = {p.name:sha(p) for p in dest.iterdir()}
        (dest/'package.json').write_text(json.dumps(dict(tpac=str(args.tpac), sha256=sha(args.tpac), metadata=[self.metadata], files=files)))
        return 0

    def test_disabled_does_not_write(self):
        self.config.pop('cloth_diagnostics')
        self.save_config()
        self.assertIsNone(run_pipeline(self.root))
        self.assertEqual(self.extraction_count, 0)
        self.assertFalse((self.root/'reports/cloth_diagnostics.json').exists())
        self.assertFalse((self.root/'build/cloth_simulator').exists())
        with patch.object(package_delivery, 'WORKSPACE', self.workspace):
            package_delivery.package('DemoCloth', 'v0.1.0', check_only=True)
        self.assertFalse((self.root/'dist').exists())
        self.assertEqual(self.extraction_count, 0)

    def test_cache_inputs_and_retained_runs(self):
        first = run_pipeline(self.root)
        self.assertEqual(first['status'], 'within_thresholds')
        second = run_pipeline(self.root)
        self.assertEqual(first['fingerprint'], second['fingerprint'])
        self.assertEqual(self.extraction_count, 1)
        animation = json.loads((self.root/'reports/idle.json').read_text())
        animation['input_revision'] = 2
        self.write('reports/idle.json', animation)
        third = run_pipeline(self.root)
        self.assertNotEqual(first['fingerprint'], third['fingerprint'])
        self.assertEqual(self.extraction_count, 2)
        self.assertTrue((self.root/first['run_directory']).is_dir())
        result = third['results'][0]
        picture = next(p for p in result['artifacts'] if p.endswith('worst_frame.png'))
        (self.root/picture).write_bytes(b'corrupted cached artifact')
        run_pipeline(self.root)
        self.assertEqual(self.extraction_count, 3)

    def test_package_and_source_archive_integration(self):
        self.config['source_files'] += ['mod.json']  # automatic inclusion must not duplicate entries
        self.save_config()
        original = sha(self.package)
        with patch.object(package_delivery, 'WORKSPACE', self.workspace):
            package_delivery.package('DemoCloth', 'v0.1.0', check_only=True)
            self.assertFalse((self.root/'dist').exists())
            package_delivery.package('DemoCloth', 'v0.1.0')
        self.assertEqual(self.extraction_count, 1)
        self.assertEqual(sha(self.package), original)
        with zipfile.ZipFile(self.root/'dist/DemoCloth_Source.zip') as z:
            names = z.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertIn('reports/cloth_diagnostics.json', names)
            self.assertIn('workspace_tools/cloth_simulator/pipeline.py', names)
            self.assertIn('workspace_tools/cloth_simulator/solver.py', names)
            self.assertTrue(any(p.endswith('/worst_frame.png') for p in names))
            self.assertIn('module/DemoCloth/ModuleData/capsules.xml', names)
            self.assertNotIn('build/probe/NativeClothProbe.dll', names)
            self.assertFalse(any(p.endswith('frames.npz') for p in names))
            report = json.loads(z.read('reports/cloth_diagnostics.json'))
            self.assertFalse(report['game_verified'])
        with zipfile.ZipFile(self.root/'dist/DemoCloth_Mod.zip') as z:
            self.assertEqual(z.read('DemoCloth/AssetPackages/test.tpac'), self.package.read_bytes())
            self.assertFalse(any('cloth_diagnostics' in p for p in z.namelist()))

    def test_review_mode_and_strict_gate(self):
        self.collision_x = -.2
        self.multiplier = .01
        self.write_capsule()
        report = ensure_diagnostics(self.root, self.config)
        self.assertEqual(report['status'], 'needs_review')
        self.config['cloth_diagnostics']['mode'] = 'strict'
        self.save_config()
        with patch.object(package_delivery, 'WORKSPACE', self.workspace):
            with self.assertRaises(ValueError):
                package_delivery.package('DemoCloth', 'v0.1.0')
        self.assertFalse((self.root/'dist').exists())

    def test_mapped_coverage_is_incomplete(self):
        self.mapped = True
        report = run_pipeline(self.root)
        self.assertEqual(report['status'], 'incomplete')
        self.assertIn('mapped cloth', report['results'][0]['reason'])

    def test_missing_selection_is_not_passed(self):
        self.config['cloth_diagnostics']['targets'][0]['meshes'] = ['missing_cloth']
        self.save_config()
        report = run_pipeline(self.root)
        self.assertEqual(report['status'], 'incomplete')

    def test_extraction_failure_blocks_packaging(self):
        self.extract_patch.stop()
        self.extract_patch = patch('cloth_simulator.run.extract', side_effect=ValueError('invalid TPAC'))
        self.extract_patch.start()
        with patch.object(package_delivery, 'WORKSPACE', self.workspace):
            with self.assertRaises(ValueError):
                package_delivery.package('DemoCloth', 'v0.1.0')
        self.assertFalse((self.root/'dist').exists())
        report = json.loads((self.root/'reports/cloth_diagnostics.json').read_text())
        self.assertEqual(report['status'], 'error')

    def test_cross_project_paths_rejected(self):
        outside = self.workspace/'other.txt'
        outside.write_text('not this mod')
        with self.assertRaises(ValueError):
            project_file(self.root, '../../other.txt')

    def test_inputs_changed_during_run_are_not_accepted(self):
        self.extract_patch.stop()
        def changing_extract(args):
            result = self.extract(args)
            self.package.write_bytes(self.package.read_bytes()+b'changed while diagnostic running')
            return result
        self.extract_patch = patch('cloth_simulator.run.extract', side_effect=changing_extract)
        self.extract_patch.start()
        report = run_pipeline(self.root)
        self.assertEqual(report['status'], 'error')
        self.assertTrue(any('inputs changed' in r.get('reason', '') for r in report['results']))


if __name__ == '__main__':
    unittest.main()
