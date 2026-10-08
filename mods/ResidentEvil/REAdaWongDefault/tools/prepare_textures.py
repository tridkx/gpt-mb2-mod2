"""Keep cha200 diffuse colors; decode available original same-outfit PBR maps."""
import sys,json,shutil,io,contextlib,struct
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,'D:/dsh-mod/re4-remake/tools/RE-Mesh-Editor-main')
from modules.mdf.file_re_mdf import readMDF
from modules.tex.re_tex_utils import convertTexFileToDDS
raw=Path('D:/dsh-mod/re4-remake/raw/ada');index={}
for p in raw.rglob('*.tex.*'):
    key=p.name.split('.tex.')[0].lower()
    if key not in index or p.stat().st_size>index[key].stat().st_size:index[key]=p
materials={};bindings={}
for p in (ROOT/'input').glob('*.mdf2.*'):
    with contextlib.redirect_stdout(io.StringIO()):mdf=readMDF(str(p))
    for mat in mdf.materialList:bindings[mat.materialName]={t.textureType:Path(t.texturePath.replace('\\','/')).name.split('.tex')[0].lower() for t in mat.textureList}
diffuse={};current=''
for line in (ROOT/'input/cha200/Ada_cha200_MainStory_full.mtl').read_text().splitlines():
    if line.startswith('newmtl '):current=line.split()[1]
    elif line.startswith('map_Kd '):diffuse[current]=Path(line.split()[1]).name

def decode(stem):
    if stem not in index:return None
    source=index[stem];shutil.copy2(source,ROOT/'input'/source.name)
    path=ROOT/'build'/(stem+'.dds')
    with contextlib.redirect_stdout(io.StringIO()):convertTexFileToDDS(str(source),str(path))
    buf=bytearray(path.read_bytes())
    if buf[84:88]==b'DX10':
        dxgi=struct.unpack_from('<I',buf,128)[0]
        srgb={72:71,75:74,78:77,100:99,92:91,28:27}
        if dxgi in srgb:struct.pack_into('<I',buf,128,srgb[dxgi]);path.write_bytes(buf)
    return np.array(Image.open(path).convert('RGBA'))

report=[]
for rec in json.loads((ROOT/'build/manifest.json').read_text()):
    mat=rec['material'];name=diffuse[mat];shutil.copy2(ROOT/'input/exported_textures'/name,ROOT/'tex'/name)
    info={'diffuse':name,'cutout':False,'normal':None,'specular':None}
    binds=bindings.get(mat,{});nr=decode(binds.get('NormalRoughnessMap',''))
    if nr is not None:
        n=nr.copy();n[:,:,3]=255;normal='reada_'+mat.lower()+'_normal.png';Image.fromarray(n).save(ROOT/'tex'/normal)
        spec=np.zeros_like(nr);spec[:,:,:3]=np.round((1-nr[:,:,3:4]/255)*40+8).astype('u1');spec[:,:,3]=255
        specname='reada_'+mat.lower()+'_specular.png';Image.fromarray(spec).save(ROOT/'tex'/specname)
        info.update(normal=normal,specular=specname)
    # Only use real decoded alpha, never guess a missing original hair mask.
    alpha=decode(binds.get('AlphaTranslucentOcclusionCavityMap',''))
    if alpha is not None and mat.lower().startswith(('hair','eyelash','blow')):
        a=np.array(Image.open(ROOT/'tex'/name).convert('RGBA'));mask=Image.fromarray(alpha[:,:,0]).resize((a.shape[1],a.shape[0]));a[:,:,3]=np.asarray(mask)
        name='reada_'+mat.lower()+'_diffuse.png';Image.fromarray(a).save(ROOT/'tex'/name);info.update(diffuse=name,cutout=True)
    materials[mat]=info
    report.append({'material':mat,'normal_available':nr is not None,'original_alpha_available':alpha is not None,'opaque_fallback':mat.lower().startswith(('hair','eyelash','blow')) and not info['cutout']})
(ROOT/'tex/materials.json').write_text(json.dumps(materials,indent=2))
(ROOT/'reports/material_recovery.json').write_text(json.dumps({'materials':report,'limitation':'Missing cha200 source maps use flat normal and conservative material response; missing hair/lash alpha remains opaque, not reconstructed or claimed original.'},indent=2))
print('TEXTURES_READY',sum(r['normal_available'] for r in report),'original normal maps')
