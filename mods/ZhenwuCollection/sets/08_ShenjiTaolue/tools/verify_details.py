"""Final-package seam normals, all-LOD motion, sole and cloth regression."""
from pathlib import Path
import json,sys,re,hashlib,struct
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'));sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
cfg=json.loads((ROOT/'tools/model_config.json').read_text(encoding='utf-8'))
fit=json.loads((ROOT/'reports/rig_fit.json').read_text());arrays=np.load(ROOT/'build/rig_arrays.npz')
geometry=json.loads((ROOT/'build/geometry.json').read_text())
package=ROOT/'module/ZhenwuCollection/AssetPackages/zw_shenji.tpac'
sha=hashlib.sha256(package.read_bytes()).hexdigest()
assert json.loads((ROOT/'reports/release_validation.json').read_text())['final_package_sha256']==sha
inspect=json.loads((ROOT/'reports/final_cloth.json').read_text())
visibility=json.loads((ROOT/'reports/final_visibility.json').read_text())
for m in visibility['materials']:
 key=m['Name'].removeprefix('zw_shenji_');mode=cfg['textures'][key][1]
 expected=cfg.get('material_overrides',{}).get(key,{})
 assert 'disable_vertex_color_alpha' in m['ShaderMaterialFlags']
 if mode!='opaque':
  assert abs(m['AlphaTest']-expected.get('alphaTest',.12 if key=='lash' else .20))<1e-6
  assert m['BlendMode']==expected.get('blendMode','factor')
 else:assert m['BlendMode']=='no_alpha_blend'
cloth=[]
for mm in inspect:
 for m in mm['meshes']:
  base=re.sub(r'\.b\d+$','',m['Name']);g=next(g for g in geometry if g['name']==base)
  if g['cloth']:
   profile=cfg['cloth_profiles'][g['kind']]
   assert m['Flags']==profile['flags'] and m['UnknownBool3']==profile['UnknownBool3']
   assert m['UnknownFloat1']==profile['UnknownFloat1']
   for key,value in profile['material'].items():
    actual=m['ClothingMaterial'][key]
    assert actual==value if isinstance(value,str) else abs(actual-value)<1e-6,(m['Name'],key)
   cloth.append({'mesh':m['Name'],'profile':g['kind'],'lod':m['Lod']})
  else:assert not m['Flags']
def channels(file,meshes):
 data=file.read_bytes();off=12;out={}
 for m in meshes:
  for field in range(3):
   length=struct.unpack_from('<I',data,off)[0];off+=4+length
   if field==0:off+=4
  n=m['nverts'];flags=m['flags'];off+=8+24+4+n*12
  normal=np.frombuffer(data,'<f4',n*3,off).reshape(n,3).copy() if flags&1 else None
  if flags&1:off+=n*12
  off+=n*8
  if flags&2:off+=n*8
  color=np.frombuffer(data,'u1',n*4,off).reshape(n,4).copy() if flags&4 else None
  if flags&4:off+=n*4
  if flags&8:off+=n*4
  if flags&16:off+=n*16
  if flags&32:off+=n*4
  off+=n*4+m['nidx']*4
  out[m['name']]=(normal,color)
 assert off==len(data)
 return out
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));lods=[]
for lod in range(4):
 folder=ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')
 meshes=[];extra={}
 for f in (folder/'geo').glob('*.bin'):
  local=read_geo(f);extra.update(channels(f,local));meshes+=local
 lookup={re.sub(r'\.lod\d+$','',m['name']):(m,cKDTree(m['pos'])) for m in meshes}
 normal_error=0
 for refs in fit['shared_skin_boundaries']:
  values=[]
  for name,vi in refs:
   m,tree=lookup[name];co=arrays[name+'_P'][vi];ids=tree.query_ball_point(co,2e-6)
   assert ids
   values.extend(extra[m['name']][0][ids])
  for n in values[1:]:normal_error=max(normal_error,float(np.linalg.norm(n-values[0])))
 assert normal_error<.002,(lod,'seam normal',normal_error)
 sole=lookup['zw_shenji_legs_02'][0];minz=float(sole['pos'][:,2].min())
 assert minz>=-1e-6,(lod,'shoe below floor',minz)
 for m in meshes:
  _,color=extra[m['name']];g=next(g for g in geometry if g['name']==m['name'])
  assert (color[:,3].max()>0)==g['cloth']
 motion=[]
 for label in ['idle','run','bow','riding']:
  anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
  frames=list(range(max(1,anim['start']),anim['frames'])) if label!='idle' else sorted(set(np.linspace(1,anim['frames']-1,16).astype(int).tolist()))
  edges={}
  for m in meshes:
   t=m['idx'].reshape(-1,3);e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);a,b=e.T
   lengths=np.linalg.norm(m['pos'][a]-m['pos'][b],axis=1);valid=lengths>.003
   edges[m['name']]=(e[valid],lengths[valid])
  maximum=0;seam_error=0
  for frame in frames:
   skin=skin_matrices(rig,anim,frame);posed={}
   for m in meshes:
    p=lbs(m['pos'],m['bi'],m['bw'],skin);assert np.isfinite(p).all();posed[m['name']]=p
    e,lengths=edges[m['name']];a,b=e.T
    maximum=max(maximum,float((np.linalg.norm(p[a]-p[b],axis=1)/lengths).max()))
   for refs in fit['shared_skin_boundaries']:
    points=[]
    for name,vi in refs:
     m,tree=lookup[name];_,index=tree.query(arrays[name+'_P'][vi]);points.append(posed[m['name']][index])
    seam_error=max(seam_error,float(np.max(np.linalg.norm(np.array(points)-points[0],axis=1))))
  assert maximum<4,(lod,label,'excessive extension',maximum)
  assert seam_error<3e-6,(lod,label,'moving seam',seam_error)
  motion.append({'label':label,'frames_checked':len(frames),'max_edge_extension':maximum,'max_shared_seam_error_m':seam_error})
 lods.append({'lod':lod,'max_seam_normal_difference':normal_error,'shoe_min_z_m':minz,'motions':motion})
report={'status':'pass','final_package_sha256':sha,'lods':lods,'cloth':cloth,'game_solver_used':False,'cloth_preprocess_cache_generated':False,'scope':'Actual final geometry, normals, colors and configuration; native skeletal motion only'}
(ROOT/'reports/detail_validation.json').write_text(json.dumps(report,indent=2));print('ALL_LOD_DETAILS_PASS',[(l['lod'],max(m['max_edge_extension'] for m in l['motions'])) for l in lods])
