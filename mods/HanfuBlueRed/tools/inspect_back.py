"""Expose garment rear surfaces and record dark atlas samples for local repair."""
import bpy, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
prefix=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'back_before'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
im=next(n.image for n in objects[0].data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
pixels=np.empty(len(im.pixels),dtype='f4');im.pixels.foreach_get(pixels);pixels=pixels.reshape(im.size[1],im.size[0],4)
rows=[]
for o in objects:
    o.hide_render=not o.name.startswith('hbr_body')
    if o.name not in ['hbr_body_29','hbr_body_18']:continue
    uv=o.data.uv_layers.active.data
    for f in o.data.polygons:
        u=np.array([uv[i].uv for i in f.loop_indices]);c=pixels[np.clip((u[:,1]*im.size[1]).astype(int),0,im.size[1]-1),np.clip((u[:,0]*im.size[0]).astype(int),0,im.size[0]-1),:3].mean(0)
        if c.max()<.24:
            rows.append({'object':o.name,'face':f.index,'color':c.tolist(),'center':list(f.center),'verts':list(f.vertices)})
(ROOT/'build/back_dark_faces.json').write_text(json.dumps(rows))
for mat in bpy.data.materials:
    im=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
    if not im:continue
    mat.node_tree.nodes.clear();out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');em=mat.node_tree.nodes.new('ShaderNodeEmission');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
    mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard'
s.world=bpy.data.worlds.new('Back inspection');s.world.color=(.16,.16,.16)
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=1.05;s.camera=cam
for suffix,offset in [('back',(0,-4,0)),('oblique',(-1.5,-4,0))]:
    center=Vector((0,-.04,1.1));cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(ROOT/'reports'/(prefix+'_'+suffix+'.png'));bpy.ops.render.render(write_still=True)
print('DARK_FACES',len(rows))
