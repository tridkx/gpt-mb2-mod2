import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
"""Build independent Yue Qingshu resources with native opaque/cutout material templates."""
import json,sys,uuid,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=workspace_root(ROOT);BUILD=ROOT/'build'
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/pipeline'))
from convert_textures import encode_mips
NATIVE=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
PACKAGE=ROOT/'module/YueQingShuOutfit2Race/AssetPackages/yqs2.tpac'
spec={'output':str(BUILD/'base.tpac'),'packageGuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'gpt-mb2-mod2/YueQingShuOutfit2Race/package')),'templates':{
 'mesh':{'tpac':str(NATIVE/'EmAssetPackages/armor555/armor555.tpac'),'name':'empire_legion_a'},
 'tex':{'tpac':str(NATIVE/'EmAssetPackages/Assets.tpac'),'name':'sturgia_light_armor_c'},
 'opaque':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'cloak_short'},
 'skeleton':{'tpac':str(NATIVE/'EmAssetPackages/human/human.tpac'),'name':'human_skeleton'},
 'alpha':{'tpac':str(NATIVE/'AssetPackages/materials.tpac'),'name':'battania_dress_c_alpha_mat'}},'textures':[],'materials':[],'meshes':[],'skeletons':[{'name':'yqs2_skeleton','template':'skeleton','bones':json.loads((BUILD/'skeleton_spec.json').read_text())}]}
(BUILD/'tex').mkdir(exist_ok=True);seen={}
previous=json.loads((BUILD/'spec.json').read_text()) if '--reuse-textures' in sys.argv else None
def texture(key,a,fmt,alpha=False):
    if key in seen:return seen[key]
    name='yqs2_tex_'+str(len(seen));path=BUILD/'tex'/(name+'.bc')
    if previous:
        old=previous['textures'][len(seen)];assert old['name']==name and old['format']==fmt and (old['width'],old['height'])==(a.shape[1],a.shape[0])
        assert path.exists()
        mips=old['mips']
        if (ROOT/'tex'/key).exists() and path.stat().st_mtime<(ROOT/'tex'/key).stat().st_mtime:
            blob,mips=encode_mips(a,fmt);path.write_bytes(blob)
    else:
        blob,mips=encode_mips(a,fmt);path.write_bytes(blob)
    spec['textures'].append({'name':name,'template':'tex','blob':str(path),'width':a.shape[1],'height':a.shape[0],'mips':mips,'format':fmt,'flags':[],'systemFlags':['has_alpha'] if alpha else []});seen[key]=name;return name
flat=np.full((64,64,4),255,'u1');flat[:]=[128,128,255,255];fn=texture('flatnormal',flat,'BC5')
flat[:]=[0,64,255,255];fs=texture('flatspecular',flat,'DXT1')
for mat,info in json.loads((ROOT/'tex/materials.json').read_text()).items():
    cut=info['cutout'];a=np.array(Image.open(ROOT/'tex'/info['diffuse']).convert('RGBA'))
    d=texture(info['diffuse'],a,'DXT5' if cut else 'DXT1',cut)
    n=texture(info['normal'],np.array(Image.open(ROOT/'tex'/info['normal']).convert('RGBA')),'BC5') if info['normal'] else fn
    s=texture(info['specular'],np.array(Image.open(ROOT/'tex'/info['specular']).convert('RGBA')),'DXT1') if info['specular'] else fs
    row={'name':'yqs2_'+mat.lower(),'template':'alpha' if cut else 'opaque','shaderMaterialFlags':['use_specular','disable_vertex_color_alpha']+(['alpha_test'] if cut else []),'textures':{'0':d,'1':n,'2':n,'4':s},'dropTextureSlots':[3,5,6,7,8,9]}
    row['flags']=['two_sided']
    if cut:row['alphaTest']=.25
    spec['materials'].append(row)
geometry=json.loads((BUILD/'geometry.json').read_text())
for part,name in [('body','yqs2_body'),('hidden','yqs2_hidden')]:
    groups=[{k:g[k] for k in ['name','geometry','material','flags','materialFlags']} for g in geometry if (g['part']!='hidden' if part=='body' else g['part']=='hidden')]
    spec['meshes'].append({'name':name,'bodyPart':'human_body','template':'mesh','groups':groups})
(BUILD/'spec.json').write_text(json.dumps(spec,indent=2));subprocess.run([MB,'build',str(BUILD/'spec.json')],check=True)
subprocess.run(['dotnet','build',str(ROOT/'tools/PackagePatch/PackagePatch.csproj'),'--ignore-failed-sources','-o',str(BUILD/'package_patch')],check=True)
subprocess.run(['dotnet',str(BUILD/'package_patch/PackagePatch.dll'),str(BUILD/'base.tpac'),str(BUILD/'uncooked.tpac'),str(BUILD/'geometry.json')],check=True)
(ROOT/'reports/material_names.json').write_text(json.dumps({r['name']:r for r in spec['materials']},indent=2))
print('PACKAGE_READY',PACKAGE)
