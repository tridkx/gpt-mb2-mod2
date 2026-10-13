"""Prepare source-backed PBR maps, explicit opacity and documented fallbacks."""
import json, shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'input/textures';out=ROOT/'tex'
def copy(name):shutil.copy2(src/name,out/name);return name
def rgba(name,alpha=None):
    a=np.array(Image.open(src/name).convert('RGBA'))
    if alpha:a[:,:,3]=np.array(Image.open(src/alpha).convert('L'))
    file='boru_'+name;Image.fromarray(a).save(out/file);return file
def orm(name):
    a=np.array(Image.open(src/name).convert('RGB'));result=a.copy();result[:,:,0]=a[:,:,2];result[:,:,1]=255-a[:,:,1];result[:,:,2]=a[:,:,0]
    file='boru_spec_'+name;Image.fromarray(result).save(out/file);return file
def solid(name,color):
    a=np.empty((64,64,4),dtype='u1');a[:]=color;Image.fromarray(a).save(out/name);return name
skin={'diffuse':copy('T_RoRu_Body_D.png'),'normal':copy('T_RoRu_Body_N.png'),'specular':orm('T_RoRu_Body_ORM.png'),'cutout':False}
cloth={'diffuse':copy('T_RoRu_2012Cloth_D.png'),'normal':copy('T_RoRu_Cloth_N.png'),'specular':solid('boru_cloth_spec.png',[0,60,255,255]),'cutout':False}
hair={'diffuse':rgba('T_Hair_D.png','T_BoRu_Hair_opacity.png'),'normal':copy('T_Hair_N.png'),'specular':solid('boru_hair_spec.png',[0,85,255,255]),'cutout':True}
iris=np.array(Image.open(src/'T_Common_Eyes_01_D.png').convert('RGB').resize((420,420),Image.Resampling.LANCZOS))
yy,xx=np.mgrid[:420,:420];mask=((xx-209.5)**2+(yy-209.5)**2)<(205**2)
eye_atlas=np.empty((1024,1024,3),'u1');eye_atlas[:]=[238,230,221]
region=eye_atlas[302:722,302:722];region[mask]=iris[mask]
Image.fromarray(eye_atlas).save(out/'boru_eye_atlas.png')
eyes={'diffuse':'boru_eye_atlas.png','normal':None,'specular':solid('boru_eyes_spec.png',[0,200,255,255]),'cutout':False}
sclera={'diffuse':solid('boru_sclera.png',[238,230,221,255]),'normal':None,'specular':eyes['specular'],'cutout':False}
lashes={'diffuse':rgba('T_RoRu_Body_D.png','T_RoRu_Body_opacity.png'),'normal':None,'specular':skin['specular'],'cutout':True}
glass={'diffuse':solid('boru_glass.png',[201,214,220,51]),'normal':None,'specular':solid('boru_glass_spec.png',[0,225,255,255]),'cutout':False,'blend':True}
accessory={'diffuse':solid('boru_accessory.png',[100,105,112,255]),'normal':None,'specular':solid('boru_accessory_spec.png',[160,110,255,255]),'cutout':False}
materials={'skin':skin,'cloth':cloth,'hair':hair,'eyes':eyes,'sclera':sclera,'lashes':lashes,'mouth':skin.copy(),'glass':glass,'accessory':accessory}
(out/'materials.json').write_text(json.dumps(materials,indent=2))
(ROOT/'reports/material_recovery.json').write_text(json.dumps({'body':'Original T_RoRu_Body_D/N/ORM; no global body opacity because its mask contains nontransparent coverage data.','cloth':'Original T_RoRu_2012Cloth_D and T_RoRu_Cloth_N; no matching 2012 ORM supplied, conservative dielectric fallback.','hair':'Original shared T_Hair_D/N with BoRu original opacity packed into diffuse alpha; no generated recoloring.','eyes':'Original iris disc placed in a sclera atlas; planar corneal UV prevents the pupil covering the entire eye. Flat normal and conservative gloss. Separate sclera and original-opacity lash cards.','mouth':'Body atlas wraps original U tile offset; original dedicated mouth shader not supplied.','glass':'Original 36-face lens mesh; neutral tint and 20 percent alpha matching original preview specification; shader appearance requires game check.','accessory':'Neutral gray for 10 untextured accessory faces; textured watch/frame pieces retain cloth atlas.','normal_convention':'Runtime DirectX maps retained; Blender preview flips green for its tangent convention.','orm_conversion':'Unreal [AO,roughness,metallic] to Bannerlord [metallic,1-roughness,AO].'},indent=2))
print('TEXTURES_READY',list(materials))
report_path=ROOT/'reports/material_recovery.json';report=json.loads(report_path.read_text())
report['glass']='Original 36-face lens geometry and 20 percent alpha. Sorted forward transparency, no opaque depth write or shadow, render order 1; actual game transparency must be retested.'
report_path.write_text(json.dumps(report,indent=2))
