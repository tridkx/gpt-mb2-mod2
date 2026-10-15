"""Build independent Emilie resources with native opaque/cutout material templates."""
import json,sys,uuid,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir());BUILD=ROOT/'build'
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/pipeline'))
from convert_textures import encode_mips
NATIVE=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
PACKAGE=ROOT/'module/EmilieRace/AssetPackages/emilie.tpac'
spec={'output':str(BUILD/'base.tpac'),'packageGuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'gpt-mb2-mod2/EmilieRace/package')),'templates':{
 'mesh':{'tpac':str(NATIVE/'EmAssetPackages/armor555/armor555.tpac'),'name':'empire_legion_a'},
 'tex':{'tpac':str(NATIVE/'EmAssetPackages/Assets.tpac'),'name':'sturgia_light_armor_c'},
 'opaque':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'cloak_short'},
 'alpha':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'battania_dress_c_alpha_mat'},
 'skeleton':{'tpac':str(NATIVE/'EmAssetPackages/human/human.tpac'),'name':'human_skeleton'}},'textures':[],'materials':[],'meshes':[],'skeletons':[{'name':'emilie_skeleton','template':'skeleton','bones':json.loads((BUILD/'skeleton_spec.json').read_text())}]}
(BUILD/'tex').mkdir(exist_ok=True);seen={}
previous=json.loads((BUILD/'spec.json').read_text()) if '--reuse-textures' in sys.argv else None
def texture(key,a,fmt,alpha=False):
    if key in seen:return seen[key]
    if a.shape[0]%4 or a.shape[1]%4:
        height=1<<(a.shape[0]-1).bit_length();width=1<<(a.shape[1]-1).bit_length()
        a=np.array(Image.fromarray(a).resize((width,height),Image.Resampling.LANCZOS))
    name='emilie_tex_'+str(len(seen));path=BUILD/'tex'/(name+'.bc')
    if previous:
        old=previous['textures'][len(seen)];assert old['name']==name and old['format']==fmt and (old['width'],old['height'])==(a.shape[1],a.shape[0]);assert path.is_file();mips=old['mips']
    else:
        blob,mips=encode_mips(a,fmt);path.write_bytes(blob)
    spec['textures'].append({'name':name,'template':'tex','blob':str(path),'width':a.shape[1],'height':a.shape[0],'mips':mips,'format':fmt,'flags':[],'systemFlags':['has_alpha'] if alpha else []});seen[key]=name;return name
flat=np.full((64,64,4),255,'u1');flat[:]=[128,128,255,255];fn=texture('flatnormal',flat,'BC5')
flat[:]=[12,12,12,255];fs=texture('flatspecular',flat,'DXT1')
for mat,info in json.loads((ROOT/'tex/materials.json').read_text(encoding='utf8')).items():
    config=json.loads((ROOT/'tools/model_config.json').read_text(encoding='utf8'))
    blend=info['source_material_index'] in config.get('glass_materials',[])
    cut=info['cutout'] and not blend;a=np.array(Image.open(ROOT/'tex'/info['diffuse']).convert('RGBA'))
    d=texture(info['diffuse'],a,'DXT5' if cut or blend else 'DXT1',cut or blend)
    n=texture(info['normal'],np.array(Image.open(ROOT/'tex'/info['normal']).convert('RGBA')),'BC5') if info['normal'] else fn
    s=texture(info['specular'],np.array(Image.open(ROOT/'tex'/info['specular']).convert('RGBA')),'DXT1') if info['specular'] else fs
    row={'name':'emilie_'+mat.lower(),'template':'alpha' if cut else 'opaque','shaderMaterialFlags':['use_specular','disable_vertex_color_alpha']+(['alpha_test'] if cut else []),'textures':{'0':d,'1':n,'2':n,'4':s},'dropTextureSlots':[3,5,6,7,8,9]}
    if cut:row['alphaTest']=.25
    row['flags']=['two_sided']
    row['blendMode']='no_alpha_blend'
    if blend:row.update(blendMode='factor',alphaTest=0,flags=['two_sided','dont_draw_to_gbuffer','no_modify_depth_buffer','alpha_blend_sort','dont_cast_shadow'],shaderMaterialFlags=['use_specular','disable_vertex_color_alpha'])
    spec['materials'].append(row)
geometry=json.loads((BUILD/'geometry.json').read_text())
for part,name in [('body','emilie_body'),('hidden','emilie_hidden')]:
    groups=[{k:g[k] for k in ['name','geometry','material','flags','materialFlags']} for g in geometry if (g['part']!='hidden' if part=='body' else g['part']=='hidden')]
    spec['meshes'].append({'name':name,'bodyPart':'human_body','template':'mesh','groups':groups})
(BUILD/'spec.json').write_text(json.dumps(spec,indent=2));subprocess.run([MB,'build',str(BUILD/'spec.json')],check=True)
subprocess.run(['dotnet','build',str(WORKSPACE/'tools/pmx_race_pipeline/PackagePatch/PackagePatch.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(BUILD/'patch_obj')+'/', '-o',str(BUILD/'package_patch')],check=True)
cfg=json.loads((ROOT/'tools/model_config.json').read_text(encoding='utf8'))
collision=cfg['prefix']+'_collision' if cfg['cloth_enabled'] else 'human_body'
subprocess.run(['dotnet',str(BUILD/'package_patch/PackagePatch.dll'),str(BUILD/'base.tpac'),str(BUILD/'uncooked.tpac'),str(BUILD/'geometry.json'),cfg['prefix'],collision],check=True)
if not cfg['cloth_enabled']:
    import shutil
    shutil.copy2(BUILD/'uncooked.tpac',PACKAGE)
(ROOT/'reports/material_names.json').write_text(json.dumps({r['name']:r for r in spec['materials']},indent=2))
print('UNCOOKED_PACKAGE_READY',BUILD/'uncooked.tpac')
