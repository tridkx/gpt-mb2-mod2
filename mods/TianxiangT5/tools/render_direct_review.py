"""Native skinning and cloth masks only; no simulated game-physics prediction."""
import bpy,json,numpy as np,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangT5_Rigged.blend'))
meshes={m['name']:m for m in json.loads((ROOT/'build/direct_cloth/final.json').read_text()) if m['lod']==0}
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith('_cloth_preview')]
matches={}
for o in objects:
    p=np.array(meshes[o.name]['pos']);s=np.array([v.co for v in o.data.vertices])
    matches[o.name]=np.array([np.argmin(np.linalg.norm(p-v,axis=1)) for v in s])
    assert np.linalg.norm(p[matches[o.name]]-s,axis=1).max()<2e-6
    for mod in list(o.modifiers):o.modifiers.remove(mod)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20
scene.world.color=(.20,.20,.20);scene.view_settings.view_transform='Standard'
scene.render.resolution_x=850;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
for loc,energy,size in [((2,3,4),500,4),((-3,2,3),400,4),((0,-3,3),300,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.10
for label,view in [('idle','front'),('block','front'),('run','side')]:
    arrays=np.load(ROOT/f'build/direct_cloth/review_{label}.npz')
    for o in objects:
        p=arrays[o.name][matches[o.name]]
        for v,co in zip(o.data.vertices,p):v.co=co
        if o.data.has_custom_normals:o.data.normals_split_custom_set_from_vertices([v.normal[:] for v in o.data.vertices])
    allp=np.concatenate([np.array([v.co for v in o.data.vertices]) for o in objects]);center=Vector((allp.min(0)+allp.max(0))/2)
    cam.location=center+Vector((.2,4,0)) if view=='front' else center+Vector((4,.2,0))
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    if '--mask-only' not in sys.argv:
        scene.render.filepath=str(ROOT/f'reports/direct_review_{label}.png');bpy.ops.render.render(write_still=True)
# In the last pose, show which vertices are physically free. Color shows the
# alpha profile, not displacement. Gray is fixed, warm colors are freer.
for o in objects:
    mat=bpy.data.materials.new('ClothReview_'+o.name);mat.use_nodes=True;mat.node_tree.nodes.clear()
    bsdf=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');bsdf.inputs['Roughness'].default_value=.8
    output=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
    a=o.data.color_attributes.new(name='ReviewDistance',type='FLOAT_COLOR',domain='POINT')
    alpha=np.array(meshes[o.name]['color'])[matches[o.name],3]/255
    cloth=bool('uses_cloth_simulation' in meshes[o.name]['flags'])
    alpha=alpha/max(float(alpha.max()),1e-9)
    for v,val in zip(a.data,alpha):v.color=(.12+.8*val,.18+.25*(1-val),.25*(1-val),1) if cloth and val>0 else (.28,.30,.34,1)
    node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name=a.name
    mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color']);o.data.materials.clear();o.data.materials.append(mat)
scene.render.filepath=str(ROOT/'reports/direct_review_mask.png');bpy.ops.render.render(write_still=True)
