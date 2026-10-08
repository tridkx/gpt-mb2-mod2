"""Local source renders for reviewing the neck and shoulders (no game launch)."""
import bpy, json, sys, numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson, skin_matrices

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangT5_Rigged.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith('_cloth_preview')]
base={o.name:np.array([v.co for v in o.data.vertices]) for o in objects}
weights={}
for o in objects:
 w=np.zeros((len(o.data.vertices),28))
 for v in o.data.vertices:
  for g in v.groups:
   i=int(o.vertex_groups[g.group].name.rsplit('_',1)[1]);w[v.index,i]=g.weight
 weights[o.name]=w
 for m in list(o.modifiers):o.modifiers.remove(m)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.world.color=(.25,.25,.25)
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'
for loc,energy,size in [((2,3,4),450,4),((-3,1,3),350,4),((0,-3,3),350,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object
 o.data.energy=energy;o.data.shape='DISK';o.data.size=size
 o.rotation_euler=(Vector((0,0,1.3))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
rig=parse_skeljson(json.load(open(ROOT/'reports/human_skeleton.json')))
anim=parse_animjson(json.load(open(ROOT/'reports/idle.json')))
for name,skin in [('rest',None),('idle',skin_matrices(rig,anim,max(1,anim['start'])))]:
 for o in objects:
  p=base[o.name].copy()
  if skin is not None:
   h=np.column_stack([p,np.ones(len(p))]);p=np.zeros_like(p)
   for i in range(28):p+=weights[o.name][:,i,None]*(h@skin[i].T)[:,:3]
  for v,co in zip(o.data.vertices,p):v.co=co
  # Posed copies need normals recalculated rather than untransformed custom normals.
  if skin is not None:o.data.normals_split_custom_set_from_vertices([v.normal[:] for v in o.data.vertices])
 cam.data.ortho_scale=1.35;cam.location=(0,4,1.48)
 cam.rotation_euler=(Vector((0,0,1.36))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(ROOT/f'reports/review_{name}.png');bpy.ops.render.render(write_still=True)
