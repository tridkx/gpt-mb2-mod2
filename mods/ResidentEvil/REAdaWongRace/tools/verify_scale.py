"""Check a uniform skin-scale release against its preserved delivery archives."""
import hashlib
import json
from pathlib import Path
import zipfile
from lxml import etree as ET
from verify_registration import canonical, validate_registration

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate():
    cfg = json.loads((ROOT / 'tools/model_config.json').read_text())
    baseline = cfg['validation_baseline_version']
    history = ROOT / 'reports/history' / baseline
    previous_cfg = json.loads((history / 'model_config.json').read_text())
    assets_report = json.loads((history / 'release_validation.json').read_text())
    assert assets_report['status'] == 'pass'
    parser = ET.XMLParser(remove_blank_text=True, remove_comments=True)
    xml = lambda data: ET.fromstring(data, parser)
    changed = []
    for kind in ['Mod', 'Source']:
        archive = ROOT / 'dist' / f"{cfg['id']}_{baseline}_{kind}.zip"
        if not archive.exists():
            archive = ROOT / 'dist' / f"{cfg['id']}_{kind}.zip"
        with zipfile.ZipFile(archive) as z:
            if kind == 'Mod':
                old_descriptor = xml(z.read(f"{cfg['id']}/SubModule.xml"))
                assert old_descriptor.find('Version').get('value') == baseline
                module = ROOT / 'module' / cfg['id']
                files = [p for p in module.rglob('*') if p.is_file()]
                assert set(z.namelist()) == {cfg['id'] + '/' + p.relative_to(module).as_posix() for p in files}
                for path in files:
                    relative = path.relative_to(module).as_posix()
                    before = z.read(cfg['id'] + '/' + relative)
                    after = path.read_bytes()
                    if before == after:
                        continue
                    changed.append(relative)
                    old, new = xml(before), xml(after)
                    if relative == 'SubModule.xml':
                        old.find('Version').set('value', cfg['version'])
                    elif relative == 'ModuleData/skins.xml':
                        rows = old.findall('race/skin')
                        assert len(rows) == 10
                        for row in rows:
                            assert float(row.get('min_scale')) == previous_cfg['skin_min_scale']
                            row.set('min_scale', str(cfg['skin_min_scale']))
                    else:
                        raise AssertionError(('Unexpected module change', relative))
                    assert canonical(old) == canonical(new), relative
            else:
                assert json.loads(z.read('tools/model_config.json'))['version'] == baseline
                for directory in ['source', 'tex']:
                    for path in (ROOT / directory).rglob('*'):
                        if path.is_file() and path.suffix in ['.blend', '.fbx', '.png']:
                            assert sha(z.read(path.relative_to(ROOT).as_posix())) == sha(path.read_bytes()), path
    assert set(changed) == {'SubModule.xml', 'ModuleData/skins.xml'}
    package_sha = sha((ROOT / 'module' / cfg['id'] / 'AssetPackages/adar.tpac').read_bytes())
    assert package_sha == assets_report['final_package_sha256']
    registration = validate_registration(ROOT)
    report = dict(version=cfg['version'], status='pass', baseline_version=baseline,
                  previous_skin_min_scale=previous_cfg['skin_min_scale'],
                  skin_min_scale=cfg['skin_min_scale'],
                  uniform_scale_ratio=cfg['skin_min_scale'] / previous_cfg['skin_min_scale'],
                  changed_module_files=sorted(changed), final_package_sha256=package_sha,
                  tpac_source_mesh_rig_weights_textures_unchanged=True,
                  skin_variants_checked=registration['skin_variants'],
                  game_test_verified=False)
    (ROOT / 'reports/scale_validation.json').write_text(json.dumps(report, indent=2))
    release = dict(assets_report)
    release.update(version=cfg['version'], registration=registration,
                   check_scope='runtime_scale_registration_and_exact_asset_baseline_comparison',
                   baseline_package_sha256=package_sha,
                   baseline_reason=cfg['validation_baseline_reason'],
                   inherited_asset_validation=f'reports/history/{baseline}/release_validation.json',
                   scale_validation=report, game_test_verified=False)
    (ROOT / 'reports/release_validation.json').write_text(json.dumps(release, indent=2))
    return report


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
