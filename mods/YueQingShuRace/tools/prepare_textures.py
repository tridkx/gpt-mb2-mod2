"""Bake separate source opacity masks into usable diffuse alpha."""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];T=ROOT/'tex'
a=Image.open(T/'T_MAJ02_01_Hair_D.png').convert('RGBA');mask=Image.open(T/'T_MAJ02_01_Hair_alpha.png').convert('L').resize(a.size,Image.Resampling.LANCZOS);a.putalpha(mask);a.save(T/'yqs_hair_rgba.png')
mask=Image.open(T/'MAJ03_01_Eyelash_Master.png').convert('L');a=Image.new('RGBA',mask.size,(35,23,19,255));a.putalpha(mask);a.save(T/'yqs_eyebrow.png')
Image.new('RGBA',(64,64),(30,20,17,255)).save(T/'yqs_lash_solid.png')
print('TEXTURES_READY')
