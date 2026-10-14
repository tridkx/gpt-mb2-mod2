"""Explicitly invisible alpha-tested cloth driver; independent of cloth vertex alpha."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from context import config,workspace_root
def add_material(root,spec):
    c=config(root);prefix=c['prefix'];b=root/'build';w=workspace_root(root)
    sys.path.insert(0,str(w/'tools/asset_helpers/pipeline'))
    from convert_textures import encode_mips
    name=prefix+'_proxy_invisible';texture=prefix+'_proxy_zero'
    pixels=np.zeros((4,4,4),dtype='uint8');Image.fromarray(pixels).save(root/'tex/physics_proxy_invisible.png')
    blob,mips=encode_mips(pixels,'DXT5');path=b/'tex'/(texture+'.bc');path.parent.mkdir(exist_ok=True);path.write_bytes(blob)
    spec['textures'].append(dict(name=texture,template='tex',blob=str(path),width=4,height=4,mips=mips,format='DXT5',flags=[],systemFlags=['has_alpha']))
    row=dict(name=name,template='alpha',shaderMaterialFlags=['use_specular','disable_vertex_color_alpha','alpha_test'],textures={'0':texture},dropTextureSlots=[1,2,3,4,5,6,7,8,9],alphaTest=.25,flags=['two_sided','dont_cast_shadow'],blendMode='no_alpha_blend')
    spec['materials'].append(row)
    path=root/'reports/material_names.json';materials=json.loads(path.read_text());materials[name]=row;path.write_text(json.dumps(materials,indent=2))
    return name
