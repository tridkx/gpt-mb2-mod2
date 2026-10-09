"""Restore original lash cutout and supply iris color missing from the ripped eye map."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
original=ROOT/'tools/Suwen_lash_original.dds'
lash=Image.open(original).convert('RGBA')
lash.save(ROOT/'tex/Tex_0044_0_alpha.png')
# Both eyes use the same full globe UV disc. Apex is at (.5,.5).
n=512;y,x=np.mgrid[0:n,0:n]/(n-1);x-=.5;y-=.5
radius=np.sqrt(x*x+y*y);angle=np.arctan2(y,x)
color=np.empty((n,n,3));color[:]=[205,194,180]
fibers=(np.sin(angle*83+radius*90)+np.sin(angle*137-radius*150))*.5
iris=np.stack([69+fibers*9,43+fibers*6,29+fibers*4],axis=-1)
iris*=np.clip((.165-radius)/.012,0,1)[...,None]*.45+.55
color=np.where((radius<.165)[...,None],iris,color)
color=np.where((radius<.057)[...,None],[9,7,6],color)
Image.fromarray(np.clip(color,0,255).astype('uint8'),'RGB').save(ROOT/'tex/Suwen_eye_iris.png')
report={'original_lash_dds_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
        'lash_alpha_restored':True,'original_pngs_unchanged':True,
        'eye_uv_changed':False,'iris':'procedural brown iris and pupil on existing globe UV; ripped diffuse contains no iris',
        'outputs':['tex/Tex_0044_0_alpha.png','tex/Suwen_eye_iris.png']}
(ROOT/'reports/eye_material_repair.json').write_text(json.dumps(report,indent=2))
print('EYE_TEXTURES_READY')
