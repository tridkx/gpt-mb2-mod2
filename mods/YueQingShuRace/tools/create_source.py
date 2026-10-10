"""Fit the preserved default Blend to the current native human bind pose."""
import bpy,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[1]
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
anchors=np.array([ni[k] for k in landmarks]);s=source[anchors][:,[0,2]];t=target[anchors]-source[anchors]
def kernel(a,b):
 d=np.linalg.norm(a[:,None]-b[None],axis=2);return d*d*np.log(np.maximum(d,1e-12))
poly=np.column_stack([np.ones(len(s)),s]);K=kernel(s,s)+np.eye(len(s))*1e-7
system=np.block([[K,poly],[poly.T,np.zeros((3,3))]])
solution=np.linalg.solve(system,np.vstack([t,np.zeros((3,3))]))
def deform(p):
 out=p+kernel(p[:,[0,2]],s)@solution[:len(s)]+np.column_stack([np.ones(len(p)),p[:,[0,2]]])@solution[len(s):]
 h=np.clip((p[:,2]-1.425)/.08,0,1);h=h*h*(3-2*h)
 rigid=p+target[ni['head']]-source[ni['head']]
 return out*(1-h[:,None])+rigid*h[:,None]
me=ob.data;me.calc_loop_triangles();raw=np.array([ob.matrix_world@v.co for v in me.vertices]);p=raw@C
fitted=deform(p)
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
# A continuous anatomical field removes abrupt UE helper-chain changes.
# The same field is applied to skin and garments so attachments stay aligned.
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def chain_field(q,indices,values,coordinate):
 order=np.argsort(values);ids=np.array(indices)[order];values=np.array(values)[order]
 ix=np.clip(np.searchsorted(values,coordinate)-1,0,len(ids)-2);lo=ids[ix];hi=ids[ix+1]
 t=smooth(values[ix],values[ix+1],coordinate);out=np.zeros((len(q),28));out[np.arange(len(q)),lo]=1-t;out[np.arange(len(q)),hi]=t
 return out
spine=[ni[n] for n in ['pelvis','spine','spine1','spine2','neck','head']]
field=chain_field(fitted,spine,target[spine,2],fitted[:,2])
for pre,sign in [('l',-1),('r',1)]:
 ids=[ni[pre+'_'+n] for n in ['clavicle','upperarm_twist','foretwist','hand']]
 armw=chain_field(fitted,ids,np.abs(target[ids,0]),np.abs(fitted[:,0]))
 amount=smooth(.09,.23,np.abs(fitted[:,0]))*smooth(.85,1.0,fitted[:,2])*(fitted[:,0]*sign>0)
 field=field*(1-amount[:,None])+armw*amount[:,None]
legs=np.zeros_like(field);side=smooth(-.045,.045,fitted[:,0])
for pre,amount in [('l',1-side),('r',side)]:
 ids=[ni[pre+'_'+n] for n in ['thigh','calf','foot']]
 legs+=chain_field(fitted,ids,target[ids,2],fitted[:,2])*amount[:,None]
amount=1-smooth(.79,.96,fitted[:,2]);field=field*(1-amount[:,None])+legs*amount[:,None]
# Keep source semantic weights outside the upper garment. Hanging tassels
# follow their torso attachment rather than nearby moving legs without cloth.
head_materials={slot.material.name for slot in ob.material_slots if slot.material.name not in cfg['anatomical_rebind_materials']}
headverts=set(v for face in me.polygons if ob.material_slots[face.material_index].material.name in head_materials for v in face.vertices)
nonhead=np.array([i for i in range(len(p)) if i not in headverts]);amount=smooth(1.05,1.20,fitted[nonhead,2])*(1-smooth(.45,.58,np.abs(fitted[nonhead,0])))
bodyverts=set(v for face in me.polygons if ob.material_slots[face.material_index].material.name=='MI_MAJ02_01_body' for v in face.vertices)
lower=(1-smooth(.90,1.05,fitted[nonhead,2]))*(1-smooth(.25,.35,np.abs(fitted[nonhead,0])))*np.isin(nonhead,list(bodyverts));amount=np.maximum(amount,lower)
w[nonhead]=w[nonhead]*(1-amount[:,None])+field[nonhead]*amount[:,None]
coords,owner=np.unique(np.round(p,6),axis=0,return_inverse=True);average=np.zeros((len(coords),28));np.add.at(average,owner,w);average/=np.bincount(owner)[:,None];w=average[owner]
keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True)
# Every digit stays in its source pose and follows the hand; no hand morphs.
# The common spatial fit prevents clothing and skin from separating at seams.
uv=me.uv_layers.active.data;data={};manifest=[];materials={}
for mi,slot in enumerate(ob.material_slots):
 mat=slot.material;tris=[x for x in me.loop_triangles if x.material_index==mi]
 if not tris:continue
 name=mat.name
 if name in ['MI_MAJ02_01_Eye_Occlusion','MI_MAJ02_01_TearLine']:
  # These UE-only translucent overlays have no diffuse texture. The eye and
  # face surfaces remain intact; omitting the overlays avoids opaque blocks.
  continue
 nodes=mat.node_tree.nodes;imgs=[n.image.name for n in nodes if n.type=='TEX_IMAGE' and n.image]
 head=name in ['MI_MAJ02_01_hair','eyelash_new_Inst','MI_MAJ02_01_eye','MAJ02_01_Eyelash_eyebrow','MI_MAJ02_01_head','MI_MAJ02_01_mouth_Skeleton']
 diffuse=next((x for x in imgs if '_D.' in x or '_D_skin.' in x or '_eye.' in x),None)
 if name=='MAJ02_01_Eyelash_eyebrow':diffuse='yqs_eyebrow.png'
 if name=='eyelash_new_Inst':diffuse='yqs_lash_solid.png'
 assert diffuse,(name,imgs)
 normal=next((x for x in imgs if '_N.' in x or 'Normal.' in x),None)
 cut=name in ['MI_MAJ02_01_hair','MAJ02_01_Eyelash_eyebrow','MI_MAJ02_01_tassel']
 if name=='MI_MAJ02_01_hair':diffuse='yqs_hair_rgba.png'
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
 jac=np.stack([(deform(pp+np.eye(3)[i]*1e-4)-q)/1e-4 for i in range(3)],axis=2)
 nn=np.linalg.solve(jac.transpose(0,2,1),nn[:,:,None])[:,:,0];nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-12)
 objname='yqs_part_'+str(mi).zfill(2)
 for suffix,a in [('p',q),('n',nn),('uv',uvs),('w',weights),('f',faces)]:data[objname+'_'+suffix]=np.array(a,dtype='i4' if suffix=='f' else 'f4')
 manifest.append({'object':objname,'part':'body','material':name,'kind':'hair' if name=='MI_MAJ02_01_hair' else ('face' if head else 'cloth')})
np.savez_compressed(ROOT/'build/fitted_model.npz',**data)
(ROOT/'build/manifest.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'tex/materials.json').write_text(json.dumps(materials,indent=2))
(ROOT/'reports/weight_transfer.json').write_text(json.dumps({'native_bones':rig['names'],'source_landmarks':source.tolist(),'target_landmarks':target.tolist(),'rotation':C.tolist(),'height_m':float(np.ptp(fitted[:,2])),'face_fit':'Rigid head offset blended through the neck','source':'Preserved default Blend','cloth':False,'source_bones':len(arm.data.bones),'no_expression_or_hand_morphs':True},indent=2))
(ROOT/'reports/input_hashes.json').write_text(json.dumps({str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (ROOT/'input').rglob('*') if x.is_file()},indent=2,ensure_ascii=False))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name='human_skeleton'
bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0]);names=[n+'_'+str(i) for i,n in enumerate(rig['names'])]
for i,n in enumerate(names):
 b=arm.data.edit_bones.new(n);b.matrix=Matrix(rig['restWorld'][i].tolist());b.length=.03
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
 mod=o.modifiers.new('Native human binding','ARMATURE');mod.object=arm;o.parent=arm
 info=materials[rec['material']];mat=bpy.data.materials.new('yqs_'+rec['material'].lower());mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.6
 image=bpy.data.images.load(str(ROOT/'tex'/info['diffuse']),check_existing=True);image.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 if info['cutout']:mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
 if info['normal']:
  image=bpy.data.images.load(str(ROOT/'tex'/info['normal']),check_existing=True);image.colorspace_settings.name='Non-Color';image.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 mesh.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/YueQingShuRace_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/YueQingShuRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
print('SOURCE_READY',len(manifest))
