"""Bake masks referenced by this source's material nodes into diffuse alpha."""
from pathlib import Path
import json
from PIL import Image
R=Path(__file__).resolve().parents[1];T=R/'tex';cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));prefix=cfg['prefix']
for rec in json.loads((R/'reports/input_inspection.json').read_text(encoding='utf8'))['parts']:
 name=rec['material'];imgs=[x['name'] for x in rec['images']]
 if 'hair' in name.lower():
  d=next(x for x in imgs if '_D.' in x);a=next(x for x in imgs if '_alpha.' in x.lower());im=Image.open(T/d).convert('RGBA');im.putalpha(Image.open(T/a).convert('L').resize(im.size,Image.Resampling.LANCZOS));im.save(T/(prefix+'_hair_rgba.png'))
 if 'macrame' in name.lower():
  d=next(x for x in imgs if 'macrame' in x.lower() and not any(k in x.lower() for k in ['alpha','normal','metallic']));a=next(x for x in imgs if 'ALPHA' in x);im=Image.open(T/d).convert('RGBA');im.putalpha(Image.open(T/a).convert('L').resize(im.size,Image.Resampling.LANCZOS));im.save(T/(prefix+'_'+name+'_rgba.png'))
mask=Image.open(T/'MAJ03_01_Eyelash_Master.png').convert('L');im=Image.new('RGBA',mask.size,(35,23,19,255));im.putalpha(mask);im.save(T/(prefix+'_eyebrow.png'))
Image.new('RGBA',(64,64),(30,20,17,255)).save(T/(prefix+'_lash_solid.png'))
print('TEXTURES_PREPARED',cfg['id'])
