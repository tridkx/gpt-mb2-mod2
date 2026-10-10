"""Unique TPAC containing source-proportioned race body and custom bind skeleton."""
import json,sys,uuid,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build'
N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native');MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
sys.path.insert(0,str(WS/'tools/asset_helpers/pipeline'))
from convert_textures import encode_mips
(B/'tex').mkdir(exist_ok=True)
spec=dict(output=str(B/'base.tpac'),packageGuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'WuduRaceTest/v0.1.0/canglan')),templates={
    'mesh':dict(tpac=str(N/'EmAssetPackages/armor555/armor555.tpac'),name='empire_legion_a'),
    'tex':dict(tpac=str(N/'EmAssetPackages/Assets.tpac'),name='sturgia_light_armor_c'),
    'opaque':dict(tpac=str(N/'AssetPackages/materials.tpac'),name='cloak_short'),
    'alpha':dict(tpac=str(N/'AssetPackages/materials.tpac'),name='battania_dress_c_alpha_mat'),
    'skeleton':dict(tpac=str(N/'EmAssetPackages/human/human.tpac'),name='human_skeleton')},textures=[],materials=[],meshes=[],skeletons=[dict(name='wdr_skeleton',template='skeleton',bones=json.loads((B/'skeleton_spec.json').read_text()))])
def tex(name,a,fmt,alpha=False):
    blob,mips=encode_mips(a,fmt);path=B/'tex'/(name+'.bc');path.write_bytes(blob)
    spec['textures'].append(dict(name=name,template='tex',blob=str(path),width=a.shape[1],height=a.shape[0],mips=mips,format=fmt,flags=[],systemFlags=['has_alpha'] if alpha else []))
a=np.full((64,64,4),255,'u1');a[:]=[128,128,255,255];tex('wdr_flat_n',a,'BC5');a[:]=[15,15,15,255];tex('wdr_neutral_s',a,'DXT1')
seen=set()
for row in json.loads((B/'rig_manifest.json').read_text()):
    if row['material'] in seen:continue
    seen.add(row['material']);name=Path(row['texture']).stem;cut=row['cutout'];a=np.array(Image.open(R/'tex'/row['texture']).convert('RGBA'));tex('wdr_'+name,a,'DXT5' if cut else 'DXT1',cut)
    mat=dict(name=row['material'],template='alpha' if cut else 'opaque',shaderMaterialFlags=['alpha_test' if cut else 'use_specular','disable_vertex_color_alpha'],textures={'0':'wdr_'+name,'1':'wdr_flat_n','2':'wdr_flat_n','4':'wdr_neutral_s'},dropTextureSlots=[3,5,6,7,8,9])
    if cut:mat['alphaTest']=.25
    spec['materials'].append(mat)
geo=json.loads((B/'geometry.json').read_text())
for part,name in [('body','wdr_canglan_body'),('hidden','wdr_hidden')]:
    spec['meshes'].append(dict(name=name,bodyPart='human_body',template='mesh',groups=[{k:g[k] for k in ['name','geometry','material','flags','materialFlags']} for g in geo if g['part']==part]))
(B/'spec.json').write_text(json.dumps(spec,indent=2));subprocess.run([MB,'build',str(B/'spec.json')],check=True)
subprocess.run(['dotnet','build',str(R/'tools/PackagePatch/PackagePatch.csproj'),'--ignore-failed-sources','-o',str(B/'package_patch')],check=True)
subprocess.run(['dotnet',str(B/'package_patch/PackagePatch.dll'),str(B/'base.tpac'),str(R/'module/WuduRaceTest/AssetPackages/wdr.tpac')],check=True)
print('PACKAGE_READY')
