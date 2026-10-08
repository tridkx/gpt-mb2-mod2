"""Build independent Hanfu assets with the recovered original 4K atlas."""
import json,sys,uuid,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'build'
(ROOT/'module/HanfuBlueRed/AssetPackages').mkdir(parents=True,exist_ok=True)
GAME=Path(r'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord')
NATIVE=GAME/'Modules/Native';MB=Path(r'D:\mb-tools\mbtool\bin\Release\net9.0\mbtool.exe')
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/pipeline'))
from convert_textures import encode_mips
(BUILD/'tex').mkdir(exist_ok=True)
spec={'output':str(BUILD/'base.tpac'),'packageGuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'bannerlord/HanfuBlueRed/package')),'templates':{
    'mesh':{'tpac':str(NATIVE/'EmAssetPackages/armor555/armor555.tpac'),'name':'empire_legion_a'},
    'tex':{'tpac':str(NATIVE/'EmAssetPackages/Assets.tpac'),'name':'sturgia_light_armor_c'},
    'opaque':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'cloak_short'}},'textures':[],'materials':[],'meshes':[]}
def texture(name,array,fmt):
    blob,mips=encode_mips(array,fmt);path=BUILD/'tex'/(name+'.bc');path.write_bytes(blob)
    spec['textures'].append({'name':name,'template':'tex','blob':str(path),'width':array.shape[1],'height':array.shape[0],'mips':mips,'format':fmt,'flags':[],'systemFlags':[]})
texture('hbr_original_d',np.array(Image.open(ROOT/'tex/汉服女孩3d模型_basecolor.JPEG').convert('RGBA')),'DXT1')
flat=np.empty((64,64,4),dtype='u1');flat[:]=[128,128,255,255];texture('hbr_flat_n',flat,'BC5')
flat[:]=[14,14,10,255];texture('hbr_neutral_s',flat,'DXT1')
spec['materials']=[{'name':'hbr_cloth','template':'opaque','shaderMaterialFlags':['use_specular','disable_vertex_color_alpha'],'textures':{'0':'hbr_original_d','1':'hbr_flat_n','2':'hbr_flat_n','4':'hbr_neutral_s'},'dropTextureSlots':[3,5,6,7,8,9]}]
geometry=json.loads((BUILD/'geometry.json').read_text());recipe={}
for part in ['head','body','legs']:
    rows=[g for g in geometry if g['part']==part]
    spec['meshes'].append({'name':'hbr_'+part,'bodyPart':'human_body','template':'mesh','groups':[{k:g[k] for k in ['name','geometry','material','flags','materialFlags']} for g in rows]})
    recipe['hbr_'+part]={g['name']:{'kind':g['kind']} for g in rows if g['cloth']}
(BUILD/'spec.json').write_text(json.dumps(spec,indent=2));(BUILD/'cloth_recipe.json').write_text(json.dumps(recipe,indent=2))
subprocess.run([str(MB),'build',str(BUILD/'spec.json')],check=True)
subprocess.run(['dotnet',str(BUILD/'package_patch/PackagePatch.dll'),str(BUILD/'base.tpac'),str(BUILD/'cloth_recipe.json'),str(ROOT/'module/HanfuBlueRed/AssetPackages/hbr.tpac')],check=True)
print('PACKAGE_READY')
