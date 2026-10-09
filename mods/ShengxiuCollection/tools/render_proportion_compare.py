"""Same-camera final-TPAC comparisons of head/neck and grounded shoes."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'))
from georead import read_geo
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
materials={}
for key,(file,mode) in cfg['textures'].items():
 im=bpy.data.images.load(str(ROOT/'build/final_export/tex'/('sx_mingyu_'+key+'_d.png')))
 mat=bpy.data.materials.new('sx_mingyu_'+key);mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.68
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
 mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 if mode!='opaque':
  test=mat.node_tree.nodes.new('ShaderNodeMath');test.operation='GREATER_THAN';test.inputs[1].default_value=cfg.get('material_overrides',{}).get(key,{}).get('alphaTest',.2)
  mat.node_tree.links.new(tex.outputs['Alpha'],test.inputs[0])
  if key=='cloth':
   blend=mat.node_tree.nodes.new('ShaderNodeMath');blend.operation='MULTIPLY'
   mat.node_tree.links.new(tex.outputs['Alpha'],blend.inputs[0]);mat.node_tree.links.new(test.outputs[0],blend.inputs[1]);mat.node_tree.links.new(blend.outputs[0],bs.inputs['Alpha'])
  else:mat.node_tree.links.new(test.outputs[0],bs.inputs['Alpha'])
 materials[mat.name]=mat
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=800;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('World');s.world.color=(.18,.18,.18);s.view_settings.view_transform='Standard'
for loc in [(2,3,4),(-3,1,3),(0,-3,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=300;o.data.size=4
 o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'
bpy.ops.mesh.primitive_plane_add(size=8);floor=bpy.context.object;floor.name='Ground z0'
ground=bpy.data.materials.new('Ground');ground.diffuse_color=(.2,.2,.2,1);floor.data.materials.append(ground)
for label,folder in [('before',ROOT/'build/proportion_baseline_v1.0.0/final_export'),('after',ROOT/'build/final_export')]:
 objects=[]
 for f in (folder/'geo').glob('*.bin'):
  for m in read_geo(f):
   me=bpy.data.meshes.new(m['name']);me.from_pydata(m['pos'].tolist(),[],m['idx'].reshape(-1,3).tolist());me.update()
   uv=me.uv_layers.new();coords=m['uv'].copy();coords[:,1]=1-coords[:,1]
   for loop in me.loops:uv.data[loop.index].uv=coords[loop.vertex_index]
   for poly in me.polygons:poly.use_smooth=True
   o=bpy.data.objects.new(m['name'],me);bpy.context.collection.objects.link(o);me.materials.append(materials[m['material']]);objects.append(o)
 for view,center,offset,zoom in [('front',(0,0,.86),(0,4,0),2.05),('neck_side',(0,0,1.52),(4,0,0),.51),('feet_side',(0,-.02,.105),(4,0,0),.46)]:
  center=Vector(center);cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=zoom
  s.render.filepath=str(ROOT/'reports'/('proportion_'+view+'_'+label+'.png'));bpy.ops.render.render(write_still=True)
 for o in objects:bpy.data.objects.remove(o,do_unlink=True)
print('PROPORTION_COMPARISONS_READY')
