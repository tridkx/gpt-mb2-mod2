import json,sys,uuid,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];B=R/'build';N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native');MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/pipeline'))
from convert_textures import encode_mips
(B/'tex').mkdir(exist_ok=True)
spec=dict(output=str(B/'base.tpac'),packageGuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'FeifengScaleTest/package')),templates={
 'mesh':dict(tpac=str(N/'EmAssetPackages/armor555/armor555.tpac'),name='empire_legion_a'),
 'tex':dict(tpac=str(N/'EmAssetPackages/Assets.tpac'),name='sturgia_light_armor_c'),
 'opaque':dict(tpac=str(N/'AssetPackages/materials.tpac'),name='cloak_short'),
 'alpha':dict(tpac=str(N/'AssetPackages/materials.tpac'),name='battania_dress_c_alpha_mat')},textures=[],materials=[],meshes=[])
def tex(name,array,fmt,alpha=False):
 blob,mips=encode_mips(array,fmt);path=B/'tex'/(name+'.bc');path.write_bytes(blob)
 spec['textures'].append(dict(name=name,template='tex',blob=str(path),width=array.shape[1],height=array.shape[0],mips=mips,format=fmt,flags=[],systemFlags=['has_alpha'] if alpha else []))
a=np.full((64,64,4),255,'u1');a[:]=[128,128,255,255];tex('ffs_flat_n',a,'BC5');a[:]=[15,15,15,255];tex('ffs_neutral_s',a,'DXT1')
for row in json.loads((B/'material_plan.json').read_text()):
 i=row['slot'];cut=row['cutout'];a=np.array(Image.open(R/'tex'/row['texture']).convert('RGBA'));tex('ffs_d_'+str(i),a,'DXT5' if cut else 'DXT1',cut)
 material=dict(name='ffs_mat_'+str(i),template='alpha' if cut else 'opaque',shaderMaterialFlags=['alpha_test' if cut else 'use_specular','disable_vertex_color_alpha'],textures={'0':'ffs_d_'+str(i),'1':'ffs_flat_n','2':'ffs_flat_n','4':'ffs_neutral_s'},dropTextureSlots=[3,5,6,7,8,9])
 if cut:material['alphaTest']=.25
 spec['materials'].append(material)
geo=json.loads((B/'geometry.json').read_text())
for profile in ['A','B']:
 for part in ['head','body','legs']:
  spec['meshes'].append(dict(name=f'ffs_{profile}_{part}',bodyPart='human_body',template='mesh',groups=[{k:g[k] for k in ['name','geometry','material','flags','materialFlags']} for g in geo if g['profile']==profile and g['part']==part]))
(B/'spec.json').write_text(json.dumps(spec,indent=2));subprocess.run([MB,'build',str(B/'spec.json')],check=True)
subprocess.run(['dotnet','build',str(R/'tools/PackagePatch/PackagePatch.csproj'),'--ignore-failed-sources','-o',str(B/'package_patch')],check=True)
subprocess.run(['dotnet',str(B/'package_patch/PackagePatch.dll'),str(B/'base.tpac'),str(R/'module/FeifengScaleTest/AssetPackages/ffs.tpac')],check=True)
print('PACKAGE_READY')
