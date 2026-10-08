"""Record generated inputs and include the editable landscape sources in delivery."""
import hashlib
import json
from PIL import Image
from paths import ROOT, PORTRAITS


def main():
    manifest = {}
    for name, _, _ in PORTRAITS:
        path = ROOT / 'input' / (name + '_landscape_v1.png')
        image = Image.open(path)
        manifest[name] = {'input': path.relative_to(ROOT).as_posix(),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'size': list(image.size), 'mode': image.mode,
                          'generator': 'built-in image_gen', 'date': '2026-10-08',
                          'reference': 'source/' + name + '.png'}
    (ROOT / 'input/landscape_provenance.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    path = ROOT / 'mod.json'
    config = json.loads(path.read_text(encoding='utf-8'))
    additions = ['input/landscape_provenance.json', 'source/landscape_prompts.md', 'tools/record_landscape.py']
    for name, _, _ in PORTRAITS:
        additions += ['input/' + name + '_landscape_v1.png', 'source/' + name + '_landscape.png']
    config['source_files'] += [p for p in additions if p not in config['source_files']]
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
