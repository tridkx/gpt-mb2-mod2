"""Preview final TPAC geometry, not game rendering."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
groups=[g for path in (R/'build/final_export0/geo').glob('*.bin') for g in read_geo(path) if g['name'].startswith('wdr_part_')]
plan={x['material']:x for x in json.loads((R/'build/rig_manifest.json').read_text())}
run=np.load(R/'build/run_preview.npz')
for pose in ['source_rest','source_side','source_back','predicted_run','worst_run','worst_sword','worst_bow','worst_rider']:
    if pose.startswith('worst_'):posed=np.load(R/'build'/(pose[6:]+'_worst_preview.npz'))
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.render.resolution_x=700;s.render.resolution_y=1000;s.render.resolution_percentage=100
    s.world=bpy.data.worlds.new('Preview');s.world.color=(.25,.25,.25)
    bounds=[]
    for g in groups:
        p=posed[g['name']] if pose.startswith('worst_') else run[g['name']] if pose=='predicted_run' else g['pos']
        bounds.extend([p.min(axis=0),p.max(axis=0)])
        me=bpy.data.meshes.new(g['name']);me.from_pydata(p.tolist(),[],g['idx'].reshape(-1,3).tolist());me.update();ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob)
        uv=me.uv_layers.new(name='UVMap')
        for loop in me.loops:u=g['uv'][loop.vertex_index];uv.data[loop.index].uv=(u[0],1-u[1])
        for f in me.polygons:f.use_smooth=True
        info=plan[g['material']];mat=bpy.data.materials.new(g['material']);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(R/'tex'/info['texture']));mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.7
        if info['cutout']:
            threshold=mat.node_tree.nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.25;mat.node_tree.links.new(node.outputs['Alpha'],threshold.inputs[0]);mat.node_tree.links.new(threshold.outputs[0],bs.inputs['Alpha'])
        me.materials.append(mat)
    bounds=np.array(bounds);center=Vector((bounds.min(axis=0)+bounds.max(axis=0))/2);offset={'source_side':(4,0,.15),'source_back':(0,-4,.15)}.get(pose,(0,4,.15));bpy.ops.object.camera_add(location=center+Vector(offset));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.7;s.camera=cam
    for location,power,size in [((-2,3,3),350,4),((2,1,2),200,3),((0,-2,3),250,3)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(location));light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    s.view_settings.view_transform='AgX';s.render.filepath=str(R/'reports'/(pose+'.png'));bpy.ops.render.render(write_still=True)
print('OFFLINE_PREVIEWS_READY')
