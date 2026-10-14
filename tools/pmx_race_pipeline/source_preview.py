"""Inspect source shape and material colors without claiming game validation."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
import numpy as np
from context import config
def preview(root):
    c=config(root);bpy.ops.wm.open_mainfile(filepath=str(root/'source'/(c['id']+'_Rigged.blend')))
    for mat in bpy.data.materials:
        ns=mat.node_tree.nodes;im=next((n.image for n in ns if n.type=='TEX_IMAGE' and n.image),None)
        if not im:continue
        ns.clear();out=ns.new('ShaderNodeOutputMaterial');tex=ns.new('ShaderNodeTexImage');tex.image=im;em=ns.new('ShaderNodeEmission');tr=ns.new('ShaderNodeBsdfTransparent');mix=ns.new('ShaderNodeMixShader');l=mat.node_tree.links;l.new(tex.outputs['Color'],em.inputs['Color']);l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.render.resolution_x=480;s.render.resolution_y=650;s.render.resolution_percentage=100;s.render.film_transparent=True;s.view_settings.view_transform='Standard';s.world=bpy.data.worlds.new('Inspection');bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam
    p=np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices]) for o in bpy.data.objects if o.type=='MESH']);center=Vector((p.min(0)+p.max(0))/2);cam.data.ortho_scale=float(np.ptp(p[:,2]))*1.14
    for label,offset in [('front',(0,4,0)),('back',(0,-4,0))]:
        cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(root/'reports'/('source_'+label+'.png'));bpy.ops.render.render(write_still=True)
    print('SOURCE_PREVIEW',c['id'],flush=True)
