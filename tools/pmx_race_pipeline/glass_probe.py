from pathlib import Path
import json,numpy as np
from PIL import Image
from source_inventory import load
from context import SERIES,config
for ident in ['SucroseRace','XianyunRace','HuTaoLanternRace']:
    root=SERIES/ident;c,m=load(root);f=np.array(m.faces);start=0
    for i,mat in enumerate(m.materials):
        faces=f[start:start+mat.vertex_count//3];start+=len(faces)
        if i not in c['glass_materials']:continue
        a=np.array(Image.open(m.textures[mat.texture].path).convert('RGBA'));uv=np.array([v.uv for v in m.vertices]);centers=uv[faces].mean(1);x=np.clip((centers[:,0]*a.shape[1]).astype(int),0,a.shape[1]-1);y=np.clip((centers[:,1]*a.shape[0]).astype(int),0,a.shape[0]-1);alpha=a[y,x,3]
        print(ident,mat.name,'texture',m.textures[mat.texture].path,'alpha range',int(alpha.min()),int(alpha.max()),'quantiles',np.quantile(alpha,[0,.1,.5,.9,1]).tolist())
