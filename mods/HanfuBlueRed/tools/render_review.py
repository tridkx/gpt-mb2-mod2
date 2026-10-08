"""Offline source preview with actual native skeletal animation, no game solver."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.blend'))
arrays=np.load(ROOT/'build/rig_arrays.npz');rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in objects:
    for mod in list(o.modifiers):o.modifiers.remove(mod)
for mat in bpy.data.materials:
    image=next((n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
    if not image:continue
    mat.node_tree.nodes.clear();out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');em=mat.node_tree.nodes.new('ShaderNodeEmission');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.render.resolution_x=1000;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('ReviewWorld');s.world.color=(.16,.16,.16);s.view_settings.view_transform='Standard'
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.15;s.camera=cam
def render(name,position,center):
    points=np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices]) for o in objects])
    middle=(points.min(0)+points.max(0))/2
    position=Vector(position)-Vector(center)+Vector(middle);center=middle
    cam.data.ortho_scale=max(1.9,float(np.ptp(points[:,2]))*1.15)
    cam.location=position;cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/'reports'/(name+'.png'));bpy.ops.render.render(write_still=True)
render('rest_front',(0,4,.96),(0,0,.96));render('rest_back',(0,-4,.96),(0,0,.96))
render('rest_side',(4,0,.96),(0,0,.96))
for label,frame in [('idle',45),('run',8),('bow',45),('riding',8)]:
    animation=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));assert animation['have'].sum()==28
    frame=int(min(frame,animation['frames']-1));skin=skin_matrices(rig,animation,frame)
    for o in objects:
        p=arrays[o.name+'_P'];w=arrays[o.name+'_W'];idx=np.argsort(-w,axis=1)[:,:4];val=np.take_along_axis(w,idx,1);q=np.floor(val/val.sum(1,keepdims=True)*255).astype(int);q[:,0]+=255-q.sum(1)
        result=lbs(p,idx,q,skin);o.data.vertices.foreach_set('co',result.astype('f4').ravel());o.data.update()
    render(label+'_preview',(2.6,4,.98),(0,0,.98))
print('PREVIEWS_READY')
