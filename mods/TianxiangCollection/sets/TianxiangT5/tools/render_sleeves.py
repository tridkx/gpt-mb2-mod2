"""Render approximate screening data on accepted textured source geometry."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangT5_Rigged.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith('_cloth_preview')]
meshes={m['name']:m for m in json.loads((ROOT/'build/sleeve_final.json').read_text()) if m['lod']==0}
matches={}
for o in objects:
    positions=np.array(meshes[o.name]['pos']);source=np.array([v.co for v in o.data.vertices])
    matches[o.name]=np.array([np.argmin(np.linalg.norm(positions-p,axis=1)) for p in source])
    assert np.linalg.norm(positions[matches[o.name]]-source,axis=1).max()<2e-6
    for mod in list(o.modifiers):o.modifiers.remove(mod)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.world.color=(.20,.20,.20)
scene.render.resolution_x=850;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'
for loc,energy,size in [((2,3,4),500,4),((-3,2,3),400,4),((0,-3,3),300,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object
    light.data.energy=energy;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(Vector((0,0,1.2))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.85
cam.location=(.2,4,1.15);cam.rotation_euler=(Vector((0,0,1.05))-cam.location).to_track_quat('-Z','Y').to_euler()
for pose in ['idle','block','bow']:
    for variant in ['before','after']:
        data=np.load(ROOT/f'build/sleeve_preview_{variant}_{pose}.npz')
        for o in objects:
            for v,co in zip(o.data.vertices,data[o.name][matches[o.name]]):v.co=co
            if o.data.has_custom_normals:o.data.normals_split_custom_set_from_vertices([v.normal[:] for v in o.data.vertices])
        scene.render.filepath=str(ROOT/f'reports/sleeve_{variant}_{pose}.png')
        bpy.ops.render.render(write_still=True)
print('SLEEVE_PREVIEWS_READY: approximate cloth, not game physics')
