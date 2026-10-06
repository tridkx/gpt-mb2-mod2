import bpy, os, math, sys, re
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1].as_posix()
rigged='--rigged' in sys.argv
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'source/TianxiangT5_Rigged.blend' if rigged else 'source/inspection.blend'))
for image in bpy.data.images:
    if image.packed_file: continue
    name=os.path.basename(image.filepath.replace('\\','/'))
    texture=os.path.join(ROOT,'tex',name)
    if not os.path.isfile(texture): texture=os.path.join(ROOT,'tex',re.sub(r'\.\d{3}$','',image.name))
    if os.path.isfile(texture):
        image.filepath=texture; image.reload()
for o in bpy.context.scene.objects:
    if o.type=='MESH' and not rigged:
        o.scale*=0.01
for m in bpy.data.materials:
    if not m.use_nodes: continue
    bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bs:
        bs.inputs['Roughness'].default_value=0.7
        bs.inputs['Metallic'].default_value=0
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.world.color=(0.25,0.25,0.25)
scene.render.resolution_x=800
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'
for loc,energy,size in [((2,3,4),450,4),((-3,1,3),350,4),((0,-3,3),350,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    light=bpy.context.object; light.data.energy=energy; light.data.shape='DISK'; light.data.size=size
    light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add()
camera=bpy.context.object; camera.data.type='ORTHO'; camera.data.ortho_scale=1.95
scene.camera=camera
for name,loc in [('front',(0,4,1.0)),('back',(0,-4,1.0)),('side',(4,0,1.0))]:
    camera.location=loc; camera.rotation_euler=(Vector((0,0,0.85))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=os.path.join(ROOT,'reports',('rigged_' if rigged else 'original_')+name+'.png')
    bpy.ops.render.render(write_still=True)
