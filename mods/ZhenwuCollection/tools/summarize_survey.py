"""Texture integrity, source manifest and original-preview contact sheet."""
import json, hashlib
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'reports/source_survey.json').read_text(encoding='utf-8'))
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 24)
sheet = Image.new('RGB', (1440, 1120), '#e9e9ee')
draw = ImageDraw.Draw(sheet)
draw.text((25, 12), '真武少女八套 · 原始模型预览（尚未制作骑砍装备）', font=font, fill='#242430')
for i, row in enumerate(data['sets']):
    folder = Path(row['source'])
    textures = []
    for path in sorted((folder/'tex').glob('*.png')):
        with Image.open(path) as im:
            im.load()
            a = np.asarray(im.convert('RGBA'))[:,:,3]
            textures.append({'name':path.name, 'size':list(im.size), 'mode':im.mode, 'alpha_min':int(a.min()), 'alpha_max':int(a.max()), 'nonopaque_fraction':float(np.mean(a<255)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    row['textures'] = textures
    row['source_manifest'] = [{'file':str(p.relative_to(folder)), 'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(folder.rglob('*')) if p.is_file()]
    x, y = (i%4)*360, 60+(i//4)*530
    with Image.open(folder/'preview/model_front.png') as im:
        thumb = ImageOps.contain(im.convert('RGB'), (350, 470))
        sheet.paste(thumb, (x+(360-thumb.width)//2, y))
    draw.text((x+22,y+477), row['name'], font=font, fill='#242430')
(ROOT/'reports/source_survey.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
sheet.save(ROOT/'reports/source_overview.jpg', quality=90)
for row in data['sets']:
    v = row['variants'][0]
    print(row['name'], 'textures',len(row['textures']), 'sizes',sorted(set(tuple(t['size']) for t in row['textures'])), 'transparent',[t['name'] for t in row['textures'] if t['alpha_min']<255], 'uv',all(m['uv_layers'] for m in v['meshes']), 'weighted',sum(m['weighted_vertices'] for m in v['meshes']), 'finite',all(m['finite'] for m in v['meshes']), 'prior_unresolved',row['prior_unresolved'])
