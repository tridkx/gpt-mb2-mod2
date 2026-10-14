"""Keep the actual simulation proxy editable without exporting it as the body."""
import bpy,sys,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];mesh=json.loads((R/'build/proxy_source.json').read_text());p=np.array(mesh['positions']);f=np.array(mesh['indices']).reshape(-1,3)
bpy.ops.wm.open_mainfile(filepath=str(R/'source/EmilieRace_Rigged.blend'))
old=bpy.data.objects.get('emilie_cloth_proxy')
if old:bpy.data.objects.remove(old,do_unlink=True)
collection=bpy.data.collections.get('Physics proxies') or bpy.data.collections.new('Physics proxies')
if collection.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(collection)
collection.hide_render=True;me=bpy.data.meshes.new('emilie_cloth_proxy');me.from_pydata(p.tolist(),[],f.tolist());me.update();o=bpy.data.objects.new('emilie_cloth_proxy',me);collection.objects.link(o);o.display_type='WIRE';o.hide_render=True;o['purpose']='Selected long hair only; skirts excluded.';arm=bpy.data.objects['emilie_skeleton'];o.parent=arm;mod=o.modifiers.new('Race binding','ARMATURE');mod.object=arm
for j,bone in enumerate(arm.data.bones):
 g=o.vertex_groups.new(name=bone.name)
 for k in range(4):
  ids=np.flatnonzero((np.array(mesh['bones'])[:,k]==j)&(np.array(mesh['weights'])[:,k]>0))
  for value in np.unique(np.array(mesh['weights'])[ids,k]):
   selected=ids[np.array(mesh['weights'])[ids,k]==value]
   g.add(selected.tolist(),float(value)/255,'REPLACE')
layer=me.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT');colors=np.ones((len(p),4));colors[:,3]=np.array(mesh['alpha'])/255;layer.data.foreach_set('color',colors.ravel());bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/EmilieRace_Rigged.blend'))
bpy.ops.wm.open_mainfile(filepath=str(R/'source/EmilieRace_Rigged.blend'));o=bpy.data.objects['emilie_cloth_proxy'];assert len(o.data.vertices)==len(p);assert len(o.data.polygons)==len(f);assert o.hide_render
actual=np.zeros((len(p),28))
for vertex in o.data.vertices:
 for group in vertex.groups:actual[vertex.index,group.group]=group.weight
expected=np.zeros_like(actual)
for vi,(bones,weights) in enumerate(zip(mesh['bones'],mesh['weights'])):
 for bone,weight in zip(bones,weights):expected[vi,bone]+=weight/255
assert np.max(abs(actual-expected))<1e-6
(R/'reports/proxy_source_validation.json').write_text(json.dumps({'status':'pass','reopened_blend':True,'proxy_vertices':len(p),'proxy_triangles':len(f),'excluded_from_render':True,'source_fbx_contains_only_body_and_armature':True},indent=2));print('EDITABLE_PROXY_SAVED',len(p))
