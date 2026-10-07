"""Review proportion change with the same camera, plus native skinning poses."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/no_cloth'
for kind in ['baseline','final']:
 bpy.ops.wm.open_mainfile(filepath=str(OUT/'baseline.blend' if kind=='baseline' else ROOT/'source/TianxiangT5_Rigged.blend'))
 for o in list(bpy.data.objects):
  if o.type in {'CAMERA','LIGHT'} or o.name.endswith('_cloth_preview'):bpy.data.objects.remove(o,do_unlink=True)
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];matches={};data={m['name']:m for m in json.loads((OUT/(kind+'.json')).read_text()) if m['lod']==0}
 for o in objects:
  for mod in list(o.modifiers):o.modifiers.remove(mod)
  o.hide_render=False;o.hide_set(False)
  if kind=='final':
   p=np.array(data[o.name]['pos']);s=np.array([v.co for v in o.data.vertices]);matches[o.name]=np.array([np.argmin(np.linalg.norm(p-v,axis=1)) for v in s]);assert np.linalg.norm(p[matches[o.name]]-s,axis=1).max()<2e-6
 # Packed images allow the immutable baseline to render from its cached location.
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.world.color=(.2,.2,.2);scene.view_settings.view_transform='Standard'
 scene.render.resolution_x=600;scene.render.resolution_y=850;scene.render.resolution_percentage=100
 for loc,energy in [((2,3,4),500),((-3,2,3),400),((0,-3,3),300)]:
  bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=4;light.rotation_euler=(Vector((0,0,1.2))-light.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.95
 views=[('rest','front')] if kind=='baseline' else [('rest','front'),('rest','side'),('run','side'),('bow','front'),('riding','front')]
 originals={o.name:np.array([v.co for v in o.data.vertices]) for o in objects}
 for pose,view in views:
  if pose!='rest':arrays=np.load(OUT/f'review_{pose}.npz')
  for o in objects:
   p=originals[o.name] if pose=='rest' else arrays[o.name][matches[o.name]]
   for v,co in zip(o.data.vertices,p):v.co=co
   o.data.update()
   if pose!='rest':o.data.normals_split_custom_set_from_vertices([v.normal[:] for v in o.data.vertices])
  center=Vector((0,0,.85));cam.location=center+Vector((0,4,0)) if view=='front' else center+Vector((4,0,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  scene.render.filepath=str(ROOT/f'reports/appearance_{kind}_{pose}_{view}.png');bpy.ops.render.render(write_still=True)
print('APPEARANCE_REVIEW_READY')
