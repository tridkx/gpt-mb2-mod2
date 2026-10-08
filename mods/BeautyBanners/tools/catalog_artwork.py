"""Record the approved nine-artwork catalog without changing the artwork."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def main():
    artwork = []
    variants = [
        ('ol_landscape', 'OL / landscape', 7101, 'ol_landscape_v1.png', 'transparent_landscape'),
        ('qipao_landscape', 'Qipao / landscape', 7102, 'qipao_landscape_v1.png', 'transparent_landscape'),
        ('hanfu_landscape', 'Hanfu / landscape', 7103, 'hanfu_landscape_v1.png', 'transparent_landscape'),
        ('ol', 'OL / portrait', 7104, 'ol_original.png', 'portrait'),
        ('qipao', 'Qipao / portrait', 7105, 'qipao_original.png', 'portrait'),
        ('hanfu', 'Hanfu / portrait', 7106, 'hanfu_original.png', 'portrait'),
        ('cyberpunk', 'Cyberpunk / city', 7107, 'cyberpunk_original.png', 'background_landscape'),
        ('anime', 'Anime / sunset', 7108, 'anime_original.png', 'background_landscape'),
        ('tang', 'Tang Hanfu / garden', 7109, 'tang_original.png', 'background_landscape'),
    ]
    for name, label, icon_id, filename, kind in variants:
        path = ROOT / 'input' / filename
        with Image.open(path) as image:
            size = list(image.size)
        artwork.append({'name': name, 'label': label, 'icon_id': icon_id, 'kind': kind,
                        'input': 'input/' + filename, 'source': 'source/' + name + '.png',
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'size': size})
    (ROOT / 'input/approved_artwork.json').write_text(json.dumps(
        {'date': '2026-10-08', 'generator': 'built-in image_gen', 'artwork': artwork},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    path = ROOT / 'mod.json'
    config = json.loads(path.read_text(encoding='utf-8'))
    additions = ['input/approved_artwork.json', 'source/background_prompts.md', 'tools/catalog_artwork.py']
    for item in artwork:
        additions += [item['input'], item['source']]
    config['source_files'] += [p for p in additions if p not in config['source_files']]
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
