"""Render final hand morph channels close up; this is not in-game validation."""
import bpy,json
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
data=json.loads((R/'build/final_hand_probe.json').read_text());mesh=next(m for m in data if m['Lod']==0)
p=np.array(mesh['positions']);faces=np.array(mesh['indices']).reshape(-1,3)
mapping=np.array(mesh['edit_vertex_position_indices']);frames=mesh['frames']
for index in [0,3,13,25]:
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
    s.world=bpy.data.worlds.new('Hand review');s.world.color=(.3,.3,.3)
    points=np.array(frames[index]['positions'])[:,:3][mapping]
    me=bpy.data.meshes.new('Hands');me.from_pydata(points.tolist(),[],faces.tolist());me.update();ob=bpy.data.objects.new('Hands',me);bpy.context.collection.objects.link(ob)
    for face in me.polygons:face.use_smooth=True
    mat=bpy.data.materials.new('Hand clay');mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.6,.38,.25,1);me.materials.append(mat)
    q=p[p[:,0]>0];center=Vector((q.min(0)+q.max(0))/2)
    bpy.ops.object.camera_add(location=center+Vector((.05,.25,.12)));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.17;s.camera=cam
    for location,power in [((.1,.2,.3),8),((-.1,-.1,.2),4)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(location));light=bpy.context.object;light.data.energy=power;light.data.size=.2;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    s.view_settings.view_transform='AgX';s.render.filepath=str(R/'reports'/f'hand_pose_{index:02d}.png');bpy.ops.render.render(write_still=True)
print('FINAL_HAND_PREVIEWS_READY')
