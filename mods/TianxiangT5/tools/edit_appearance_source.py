"""Apply the same position transform to the editable historical source."""
from pathlib import Path
import bpy,bmesh,json,numpy as np,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from appearance_transform import CONFIG,deform
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'build/no_cloth/baseline.blend'))
for o in list(bpy.data.objects):
 if o.name.endswith('_cloth_preview'):bpy.data.objects.remove(o,do_unlink=True)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==14
baseline=json.loads((ROOT/'build/no_cloth/baseline.json').read_text());recipe=json.loads((ROOT/'build/no_cloth/recipe.json').read_text())
for o in objects:
 for mod in list(o.modifiers):
  if mod.type=='CLOTH':o.modifiers.remove(mod)
 o['cloth_enabled']=False;o['cloth_route']='disabled; skeletal skinning only'
 if o.name=='tx5_body_00':
  old=next(m for m in baseline if m['name']==o.name);keep=recipe['meshes'][o.name]['keep'];removed=np.setdiff1d(np.arange(len(old['pos'])),keep);tails=np.array(old['pos'])[removed]
  bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();delete=[v for v in bm.verts if np.linalg.norm(tails-np.array(v.co),axis=1).min()<2e-6]
  assert len(delete)>200;bmesh.ops.delete(bm,geom=delete,context='VERTS');bm.to_mesh(o.data);bm.free()
 if o.name.startswith('tx5_head_'):
  me=o.data;p=np.array([v.co for v in me.vertices]);normals=np.array([n.vector for n in me.corner_normals]);loopid=np.array([l.vertex_index for l in me.loops]);dest,J=deform(p,o.name)
  transformed=np.einsum('nij,nj->ni',np.linalg.inv(J[loopid]).transpose(0,2,1),normals);transformed/=np.linalg.norm(transformed,axis=1)[:,None]
  for v,co in zip(me.vertices,dest):v.co=co
  me.update();me.normals_split_custom_set(transformed.tolist());o['head_scale']=CONFIG['head_scale']
thigh=bpy.data.objects['tx5_legs_06'];skin=bpy.data.objects['tx5_body_07'].data.materials[0].copy();skin.name='tx5_skin_thigh_body_D';skin.use_nodes=True
for node in skin.node_tree.nodes:
 if node.type=='TEX_IMAGE':
  image=bpy.data.images.load(str(ROOT/'tex/body_D.png'),check_existing=True);node.image=image
 if node.type=='BSDF_PRINCIPLED':
  for link in list(node.inputs['Alpha'].links):skin.node_tree.links.remove(link)
  node.inputs['Alpha'].default_value=1.0
thigh.data.materials.clear();thigh.data.materials.append(skin)
for image in bpy.data.images:
 if image.source=='FILE':
  path=ROOT/'tex'/Path(image.filepath.replace('\\','/')).name
  assert path.is_file(),path
  image.filepath=str(path);image.reload();image.pack();image.filepath='//../tex/'+path.name
bpy.context.scene['release_version']=CONFIG['version'];bpy.context.scene['cloth_enabled']=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/TianxiangT5_Rigged.blend'),relative_remap=False)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
 if o.type in {'MESH','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/TianxiangT5_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',axis_forward='-Z',axis_up='Y')
print('APPEARANCE_SOURCE_READY')

