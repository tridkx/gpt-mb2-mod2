import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
"""Preserve source geometry and fit custom race joint pivots to source anatomy."""
import bpy,json,sys,hashlib

import numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=workspace_root(ROOT)
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
target=rig['restWorld'][:,:3,3];ni={n:i for i,n in enumerate(rig['names'])}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/cfg['source_blend']))
ob=next(o for o in bpy.data.objects if o.type=='MESH');arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
C=np.diag([-1.,-1.,1.])
anatomy={b.name:np.array(arm.matrix_world@b.head_local)@C for b in arm.data.bones}
mapping={'Bip001-Pelvis':'pelvis','Bip001-Spine':'spine','Bip001-Spine1':'spine1','Bip001-Spine2':'spine2','Bip001-Neck':'neck','Bip001-Head':'head'}
landmarks={v:k for k,v in mapping.items()}
for side,pre in [('L','l'),('R','r')]:
 for src,dst in [('Thigh','thigh'),('Calf','calf'),('Foot','foot'),('Toe0','toe0'),('Clavicle','clavicle'),('UpperArm','upperarm_twist'),('Forearm','foretwist'),('Hand','hand')]:
  mapping[f'Bip001-{side}-{src}']=f'{pre}_{dst}';landmarks[f'{pre}_{dst}']=f'Bip001-{side}-{src}'
 mapping[f'Bip001-{side}-ForeTwist']=f'{pre}_foretwist'
source=target.copy()
for dst,src in landmarks.items():source[ni[dst]]=anatomy[src]
# Geometry is never warped to native anatomy. Only rotate the entire source.
for pre in ['l','r']:
 for mid,a,b in [('upperarm_twist1','upperarm_twist','foretwist'),('foretwist1','foretwist','hand')]:
  source[ni[pre+'_'+mid]]=(source[ni[pre+'_'+a]]+source[ni[pre+'_'+b]])/2
 # Finger pivots come from the original hand, without changing its shape.
 source[ni[pre+'_finger0']]=anatomy['Bip001-'+pre.upper()+'-Finger0']
world=rig['restWorld'].copy();world[:,:3,3]=source
alignment=[]
for i,start,end in [(15,15,17),(16,15,17),(17,17,19),(18,17,19),(22,22,24),(23,22,24),(24,24,26),(25,24,26)]:
 a=world[i,:3,0].copy();v=source[end]-source[start];v/=np.linalg.norm(v);cross=np.cross(a,v);c=float(a@v);assert c>-.99
 K=np.array([[0,-cross[2],cross[1]],[cross[2],0,-cross[0]],[-cross[1],cross[0],0]]);Q=np.eye(3)+K+K@K/(1+c);world[i,:3,:3]=Q@world[i,:3,:3]
 alignment.append(dict(bone=rig['names'][i],rotation_degrees=float(np.degrees(np.arccos(np.clip(c,-1,1))))))
(ROOT/'reports/arm_bind_alignment.json').write_text(json.dumps(dict(enabled=True,bones=alignment,joint_positions_unchanged=True),indent=2))
local=np.array([world[i] if parent<0 else np.linalg.inv(world[parent])@world[i] for i,parent in enumerate(rig['parent'])])
bones=[]
for i,bone in enumerate(json.loads((ROOT/'reports/human_skeleton.json').read_text())['bones']):
 matrix=np.array(bone['rest']).reshape(4,4).T;matrix[:3,:3]=local[i,:3,:3];matrix[:3,3]=local[i,:3,3]
 bones.append(dict(name=bone['name'],parent=bone['parent'],rest=matrix.T.reshape(-1).tolist()))
(ROOT/'build/skeleton_spec.json').write_text(json.dumps(bones,indent=2))
me=ob.data;me.calc_loop_triangles();raw=np.array([ob.matrix_world@v.co for v in me.vertices]);p=raw@C
fitted=p.copy()
# Preserve original weights where semantic bones correspond; face, fingers,
# hair and garment helper chains collapse to their nearest supported ancestor.
w=np.zeros((len(p),28));group_map={}
for g in ob.vertex_groups:
 b=arm.data.bones.get(g.name)
 while b and b.name not in mapping:b=b.parent
 group_map[g.index]=ni[mapping[b.name]] if b else ni['pelvis']
for v in me.vertices:
 for g in v.groups:w[v.index,group_map[g.group]]+=g.weight
assert np.all(w.sum(1)>0);w/=w.sum(1,keepdims=True)
from refine_weights import refine
w,refinement=refine(me,ob,p,w,cfg,source,ni)
(ROOT/'reports/weight_refinement.json').write_text(json.dumps(refinement,indent=2))
coords,owner=np.unique(np.round(p,6),axis=0,return_inverse=True);average=np.zeros((len(coords),28));np.add.at(average,owner,w);average/=np.bincount(owner)[:,None];w=average[owner]
keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True)
# Every digit stays in its source pose and follows the hand; no hand morphs.
# Common weights at shared source coordinates keep material boundaries together.
uv=me.uv_layers.active.data;data={};manifest=[];materials={}
for mi,slot in enumerate(ob.material_slots):
 mat=slot.material;tris=[x for x in me.loop_triangles if x.material_index==mi]
 if not tris:continue
 name=mat.name
 if 'Eye_Occlusion' in name or 'TearLine' in name:continue
 nodes=mat.node_tree.nodes;imgs=[n.image.name for n in nodes if n.type=='TEX_IMAGE' and n.image]
 head=any(k in name.lower() for k in ['hair','eyelash','eyebrow','eye','head','mouth'])
 diffuse=next((x for x in imgs if '_D_skin.' in x or '_BaseColor.' in x or '_D.' in x or '_eye.' in x),None)
 normal=next((x for x in imgs if '_N.' in x or '_Normal.' in x),None)
 alpha=next((x for x in imgs if '_alpha.' in x.lower()),None)
 cut=False
 if 'hair' in name.lower() and diffuse and alpha:diffuse=cfg['prefix']+'_hair_rgba.png';cut=True
 elif 'eyebrow' in name.lower() or 'Eyelash_Master' in name:diffuse=cfg['prefix']+'_eyebrow.png';cut=True
 elif 'eyelash' in name.lower():diffuse=next((x for x in imgs if 'eyelash' in x.lower()),cfg['prefix']+'_lash_solid.png')
 elif 'macrame' in name.lower():diffuse=cfg['prefix']+'_'+name+'_rgba.png';cut=True
 if not diffuse and name=='MAJ03_02_cloth3':
  bs=nodes.get('Principled BSDF');colour=list(bs.inputs['Base Color'].default_value)
  diffuse=cfg['prefix']+'_fur_base.png';image=bpy.data.images.new('Fur base',width=64,height=64);image.generated_color=colour;image.filepath_raw=str(ROOT/'tex'/diffuse);image.file_format='PNG';image.save()
 assert diffuse,(name,imgs)
 materials[name]={'diffuse':diffuse,'normal':normal,'specular':None,'cutout':cut}
 vertices=[];normals=[];uvs=[];weights=[];faces=[];dedup={}
 for tri in tris:
  face=[]
  for li in tri.loops:
   vi=me.loops[li].vertex_index;u=tuple(uv[li].uv);norm=np.array(me.corner_normals[li].vector)@C
   key=(vi,u,tuple(np.round(norm,6)))
   if key not in dedup:
    dedup[key]=len(vertices);vertices.append(fitted[vi]);uvs.append(u);weights.append(w[vi]);normals.append(norm)
   face.append(dedup[key])
  faces.append(face)
 q=np.array(vertices);nn=np.array(normals);pp=p[[k[0] for k in dedup]]
 nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-12)
 objname='bmq_part_'+str(mi).zfill(2)
 for suffix,a in [('p',q),('n',nn),('uv',uvs),('w',weights),('f',faces)]:data[objname+'_'+suffix]=np.array(a,dtype='i4' if suffix=='f' else 'f4')
 manifest.append({'object':objname,'part':'body','material':name,'kind':'hair' if 'hair' in name.lower() else ('face' if head else 'cloth')})
np.savez_compressed(ROOT/'build/fitted_model.npz',**data)
(ROOT/'build/manifest.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'tex/materials.json').write_text(json.dumps(materials,indent=2))
(ROOT/'reports/weight_transfer.json').write_text(json.dumps({'native_bones':rig['names'],'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'rotation':C.tolist(),'height_m':float(np.ptp(fitted[:,2])),'source_geometry_max_error_m':float(np.abs(fitted-p).max()),'source_proportions_preserved':True,'face_fit':'Original geometry, no shape deformation','source':cfg['source_blend'],'cloth':cfg['cloth_enabled'],'source_bones':len(arm.data.bones),'no_expression_or_hand_morphs':True},indent=2))
(ROOT/'reports/input_hashes.json').write_text(json.dumps({str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (ROOT/'input').rglob('*') if x.is_file()},indent=2,ensure_ascii=False))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name=cfg['skeleton']
bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0]);names=[n+'_'+str(i) for i,n in enumerate(rig['names'])]
for i,n in enumerate(names):
 b=arm.data.edit_bones.new(n);b.matrix=Matrix(world[i].tolist());b.length=.03
for i,n in enumerate(names):
 if rig['parent'][i]>=0:arm.data.edit_bones[n].parent=arm.data.edit_bones[names[rig['parent'][i]]]
bpy.ops.object.mode_set(mode='OBJECT');cache={}
for rec in manifest:
 name=rec['object'];mesh=bpy.data.meshes.new(name);mesh.from_pydata(data[name+'_p'].tolist(),[],data[name+'_f'].tolist());mesh.update();layer=mesh.uv_layers.new(name='UVMap')
 for loop in mesh.loops:layer.data[loop.index].uv=data[name+'_uv'][loop.vertex_index]
 for face in mesh.polygons:face.use_smooth=True
 mesh.normals_split_custom_set_from_vertices(data[name+'_n'].tolist())
 o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
 for i,n in enumerate(names):
  group=o.vertex_groups.new(name=n)
  for vi in np.flatnonzero(data[name+'_w'][:,i]>1e-7):group.add([int(vi)],float(data[name+'_w'][vi,i]),'REPLACE')
 mod=o.modifiers.new('Source proportion race binding','ARMATURE');mod.object=arm;o.parent=arm
 info=materials[rec['material']];mat=bpy.data.materials.new('bmq_'+rec['material'].lower());mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.6
 image=bpy.data.images.load(str(ROOT/'tex'/info['diffuse']),check_existing=True);image.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 if info['cutout']:mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
 if info['normal']:
  image=bpy.data.images.load(str(ROOT/'tex'/info['normal']),check_existing=True);image.colorspace_settings.name='Non-Color';image.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 mesh.materials.append(mat)
for image in bpy.data.images:
 if image.source=='FILE':image.filepath='//../tex/'+Path(image.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/BaiMoQingRace_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/BaiMoQingRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
print('SOURCE_READY',len(manifest))
