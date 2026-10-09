"""Identical camera and native bow frame, before/after head weights from final meshes."""
import bpy,sys,runpy,json
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]/'sets'/sys.argv[-1]
sys.argv=['render_review.py','--','final','quick','face_only','face']
g=runpy.run_path(str(ROOT/'tools/render_review.py'))
objects,meshes,cam,scene=g['objects'],g['meshes'],g['cam'],g['s']
rig=g['parse_skeljson'](json.loads((ROOT/'reports/human_skeleton.json').read_text()))
anim=g['parse_animjson'](json.loads((ROOT/'reports/bow.json').read_text()));skin=g['skin_matrices'](rig,anim,12)
manifest=json.loads((ROOT/'build/rig_manifest.json').read_text());eye=next(x['object'] for x in manifest if x['texture_key']=='eye')
from mathutils.kdtree import KDTree
arrays=np.load(ROOT/'build/rig_arrays.npz')
old_weights={}
for m in meshes:
 points=arrays[m['name']+'_P'];tree=KDTree(len(points))
 for i,p in enumerate(points):tree.insert(p,i)
 tree.balance();ids=[tree.find(p)[1] for p in m['pos']]
 old_weights[m['name']]=arrays[m['name']+'_fitW'][ids]
posed=[]
for m in meshes:posed.append(g['lbs'](m['pos'],m['bi'],m['bw'],skin))
center=Vector(next(p for p,m in zip(posed,meshes) if m['name']==eye).mean(0));center.z-=.055
cam.location=center+Vector((0,3,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.46
for label in ['before','after']:
 for o,m,p in zip(objects,meshes,posed):
  if label=='before':
   w=old_weights[m['name']]
   ph=np.c_[m['pos'],np.ones(len(p))];v=np.einsum('bij,nj->nbi',skin,ph)[:,:,:3];p=np.einsum('nb,nbi->ni',w,v)
  o.data.vertices.foreach_set('co',p.astype('f4').ravel());o.data.update()
 scene.render.filepath=str(ROOT/f'reports/head_bow_{label}.png');bpy.ops.render.render(write_still=True)
(ROOT/'reports/head_preview_comparison.json').write_text(json.dumps({'frame':12,'animation':'native bow','camera_identical':True,'source':'final TPAC geometry and textures; original measured fit weights versus final quantized weights','images':['head_bow_before.png','head_bow_after.png']},indent=2))
