"""Create an isolated project scaffold without Tianxiang-specific assets."""
import argparse
import json
from package_delivery import WORKSPACE, validate_name


def create(name):
    validate_name(name)
    root = WORKSPACE / 'mods' / name
    root.mkdir(parents=True, exist_ok=False)
    for folder in ['input', 'source', 'tex', 'tools', 'build', 'reports', 'dist',
                   f'module/{name}/ModuleData', f'module/{name}/AssetPackages']:
        target = root / folder
        target.mkdir(parents=True, exist_ok=True)
        if folder.split('/')[0] not in {'build', 'dist'}:
            (target / '.gitkeep').touch()
    config = {'id': name, 'source_files': ['README.md'],
              'package': f'module/{name}/AssetPackages/{name}.tpac',
              'validation_report': 'reports/release_validation.json'}
    (root / 'mod.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    (root / 'README.md').write_text(
        f'# {name}\n\n新模组工程，尚未制作或发布。\n\n'
        '原始模型放 input/，可编辑工程放 source/，贴图放 tex/，专用脚本放 tools/。\n'
        '完成制作后创建 SubModule.xml 和 items.xml，使用自己的资源名及 GUID，'
        '并将 mod.json 的 source_files、package、validation_report 更新为实际交付文件。\n',
        encoding='utf-8')
    print(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    create(parser.parse_args().name)
