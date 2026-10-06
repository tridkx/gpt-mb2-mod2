import json,os,sys,subprocess,uuid
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
GAME=Path(r'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord')
MB=Path(r'D:\mb-tools\mbtool\bin\Release\net9.0\mbtool.exe')
NATIVE=GAME/'Modules/Native'
sys.path.insert(0,r'D:\gpt-mb2-mod\pipeline')
from convert_textures import encode_mips
build=ROOT/'build';(build/'tex').mkdir(exist_ok=True)
module=ROOT/'module/TianxiangT5';(module/'AssetPackages').mkdir(parents=True,exist_ok=True)
(module/'ModuleData').mkdir(exist_ok=True)
spec={'output':str(build/'base.tpac'),'packageGuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'gpt-mb2-mod2/TianxiangT5/2026-10-06')), 'templates':{
 'mesh':{'tpac':str(NATIVE/'EmAssetPackages/armor555/armor555.tpac'),'name':'empire_legion_a'},
 'tex':{'tpac':str(NATIVE/'EmAssetPackages/Assets.tpac'),'name':'sturgia_light_armor_c'},
 'opaque':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'cloak_short'},
 'alpha':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'battania_dress_c_alpha_mat'}},'textures':[],'materials':[],'meshes':[]}
plan={'tunic':('tunic_D-PVE.png','sheer'),'pants':('pants_D-PVE.png','sheer'),'skin':('body_D.png','opaque'),'cuff':('cuff_D.png','cutout'),'hair':('hair_D.png','cutout'),'head':('head_D.png','cutout'),'face':('face_D.png','opaque'),'eye':('eye_D.png','opaque'),'lash':('eyelash_D.png','cutout')}
def texture(name,a,fmt,alpha=False):
 blob,mips=encode_mips(a,fmt);p=build/'tex'/ (name+'.bc');p.write_bytes(blob)
 spec['textures'].append({'name':name,'template':'tex','blob':str(p),'width':a.shape[1],'height':a.shape[0],'mips':mips,'format':fmt,'flags':[],'systemFlags':['has_alpha'] if alpha else []})
flat=np.zeros((64,64,4),np.uint8);flat[:]=[128,128,255,255];texture('tx5_flat_n',flat,'BC5')
specmap=np.zeros((64,64,4),np.uint8);specmap[:]=[24,24,18,255];texture('tx5_neutral_s',specmap,'DXT1')
for name,(file,mode) in plan.items():
 a=np.array(Image.open(ROOT/'tex'/file).convert('RGBA'))
 if mode=='opaque':a[:,:,3]=255
 elif mode=='sheer':a[:,:,3]=np.round(140+a[:,:,3].astype(float)*115/255).astype('u1')
 texture('tx5_'+name+'_d',a,'DXT1' if mode=='opaque' else 'DXT5',mode!='opaque')
 # Vertex alpha stores cloth travel distance, often zero on pinned vertices.
 # Rendering must ignore it and use diffuse texture alpha for transparency.
 shader_flags=['use_specular' if mode=='opaque' else 'alpha_test','disable_vertex_color_alpha']
 mat={'name':'tx5_'+name,'template':'opaque' if mode=='opaque' else 'alpha','shaderMaterialFlags':shader_flags,'textures':{'0':'tx5_'+name+'_d','1':'tx5_flat_n','2':'tx5_flat_n','4':'tx5_neutral_s'},'dropTextureSlots':[3,5,6,7,8,9]}
 if mode!='opaque':mat['alphaTest']=.2745
 spec['materials'].append(mat)
geo=json.load(open(build/'geometry.json'))
patch={}
for part in ['head','body','legs']:
 gs=[{k:g[k] for k in ['name','geometry','material','flags','materialFlags']} for g in geo if g['part']==part]
 spec['meshes'].append({'name':'tx5_'+part,'bodyPart':'human_body','template':'mesh','groups':gs})
 patch['tx5_'+part]={'body':'human_body','clothGroups':[g['name'] for g in geo if g['part']==part and g['cloth']]}
json.dump(spec,open(build/'spec.json','w'),indent=1)
json.dump(patch,open(build/'cloth_patch.json','w'),indent=1)
subprocess.run([str(MB),'build',str(build/'spec.json')],check=True)
subprocess.run(['dotnet',str(ROOT/'tools/AssetTool/AssetTool.dll'),'patch',str(build/'base.tpac'),str(build/'cloth_patch.json'),str(module/'AssetPackages/tx5.tpac')],check=True)
print('PACKAGE_READY',module)
