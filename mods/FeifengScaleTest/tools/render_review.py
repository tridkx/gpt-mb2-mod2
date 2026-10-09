import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
groups={g['name']:g for path in (R/'build/final_export0/geo').glob('*.bin') for g in read_geo(path)}
positions=np.load(R/'build/preview_positions.npz')
for scene in ['A_rest','B_rest','B_run']:
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.render.resolution_x=700;s.render.resolution_y=1000;s.render.resolution_percentage=100
 s.world=bpy.data.worlds.new('Preview world');s.world.color=(.25,.25,.25);objects=[]
 for key in positions.files:
  if not key.startswith(scene+'__'):continue
  name=key.split('__')[1];g=groups[name];me=bpy.data.meshes.new(name);me.from_pydata(positions[key].tolist(),[],g['idx'].reshape(-1,3).tolist());me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);objects.append(ob)
  uv=me.uv_layers.new(name='UVMap')
  for loop in me.loops:u=g['uv'][loop.vertex_index];uv.data[loop.index].uv=(u[0],1-u[1])
  for f in me.polygons:f.use_smooth=True
  mat=bpy.data.materials.new(g['material']);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');node=mat.node_tree.nodes.new('ShaderNodeTexImage')
  slot=int(g['material'].rsplit('_',1)[1]);info=json.loads((R/'build/material_plan.json').read_text())[slot];node.image=bpy.data.images.load(str(R/'tex'/info['texture']));mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.6
  if info['cutout']:
   threshold=mat.node_tree.nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.25;mat.node_tree.links.new(node.outputs['Alpha'],threshold.inputs[0]);mat.node_tree.links.new(threshold.outputs[0],bs.inputs['Alpha'])
  me.materials.append(mat)
 allpoints=np.concatenate([positions[k] for k in positions.files if k.startswith(scene+'__')]);center=(allpoints.min(0)+allpoints.max(0))/2
 bpy.ops.object.camera_add(location=(3.8,7.5,3.4));camera=bpy.context.object;camera.rotation_euler=(Vector(center)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=3.1;s.camera=camera
 for location,power,size in [((-3,4,5),1000,5),((3,0,4),700,4),((0,-3,4),600,3)]:
  bpy.ops.object.light_add(type='AREA',location=location);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector(center)-light.location).to_track_quat('-Z','Y').to_euler()
 s.view_settings.view_transform='AgX';s.render.filepath=str(R/'reports'/('predicted_'+scene+'.png'));bpy.ops.render.render(write_still=True)
print('PREDICTED_PREVIEWS_READY')
