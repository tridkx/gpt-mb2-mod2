"""Build isolated TianxiangMuyu assets; preserve source texture alpha without remapping."""
import json,sys,uuid,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'build'
NATIVE=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/pipeline'))
from convert_textures import encode_mips
cfg=json.loads((ROOT/'tools/model_config.json').read_text());(BUILD/'tex').mkdir(exist_ok=True)
spec={'output':str(BUILD/'base.tpac'),'packageGuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'bannerlord/TianxiangMuyu/package')),'templates':{
    'mesh':{'tpac':str(NATIVE/'EmAssetPackages/armor555/armor555.tpac'),'name':'empire_legion_a'},
    'tex':{'tpac':str(NATIVE/'EmAssetPackages/Assets.tpac'),'name':'sturgia_light_armor_c'},
    'opaque':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'cloak_short'},
    'alpha':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'battania_dress_c_alpha_mat'}},'textures':[],'materials':[],'meshes':[]}
def texture(name,a,fmt,alpha=False):
    blob,mips=encode_mips(a,fmt);p=BUILD/'tex'/(name+'.bc');p.write_bytes(blob)
    spec['textures'].append({'name':name,'template':'tex','blob':str(p),'width':a.shape[1],'height':a.shape[0],'mips':mips,'format':fmt,'flags':[],'systemFlags':['has_alpha'] if alpha else []})
flat=np.empty((64,64,4),dtype='u1');flat[:]=[128,128,255,255];texture('my4_flat_n',flat,'BC5')
flat[:]=[18,18,12,255];texture('my4_neutral_s',flat,'DXT1')
for key,(file,mode) in cfg['textures'].items():
    a=np.array(Image.open(ROOT/'tex'/file).convert('RGBA'))
    texture('my4_'+key+'_d',a,'DXT1' if mode=='opaque' else 'DXT5',mode!='opaque')
    mat={'name':'my4_'+key,'template':'opaque' if mode=='opaque' else 'alpha','shaderMaterialFlags':['use_specular' if mode=='opaque' else 'alpha_test','disable_vertex_color_alpha'],'textures':{'0':'my4_'+key+'_d','1':'my4_flat_n','2':'my4_flat_n','4':'my4_neutral_s'},'dropTextureSlots':[3,5,6,7,8,9]}
    if mode!='opaque':mat['alphaTest']=.12 if key=='lash' else .20
    mat.update(cfg.get('material_overrides',{}).get(key,{}))
    spec['materials'].append(mat)
geometry=json.loads((BUILD/'geometry.json').read_text());recipe={}
for part in ['head','body','legs']:
    rows=[g for g in geometry if g['part']==part]
    spec['meshes'].append({'name':'my4_'+part,'bodyPart':'human_body','template':'mesh','groups':[{k:g[k] for k in ['name','geometry','material','flags','materialFlags']} for g in rows]})
    recipe['my4_'+part]={g['name']:{'kind':g['kind']} for g in rows if g['cloth']}
(BUILD/'spec.json').write_text(json.dumps(spec,indent=2));(BUILD/'cloth_recipe.json').write_text(json.dumps(recipe,indent=2))
subprocess.run([MB,'build',str(BUILD/'spec.json')],check=True)
subprocess.run(['dotnet',str(BUILD/'package_patch/PackagePatch.dll'),str(BUILD/'base.tpac'),str(BUILD/'cloth_recipe.json'),str(ROOT/'module/TianxiangMuyu/AssetPackages/my4.tpac')],check=True)
print('PACKAGE_READY')
