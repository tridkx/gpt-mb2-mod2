"""Same-camera final TPAC standing shoe previews with visible ground plane."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'D:\gpt-mb2-mod\tools');sys.path.insert(0,r'D:\gpt-mb2-mod\previewer')
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
bpy.ops.wm.read_factory_settings(use_empty=True)
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));anim=parse_animjson(json.loads((ROOT/'reports/idle.json').read_text()));skin=skin_matrices(rig,anim,1)
manifest=json.loads((ROOT/'build/rig_manifest.json').read_text());names={r['object'] for r in manifest if r['kind']=='shoe'}
image=bpy.data.images.load(str(ROOT/'build/final_export/tex/hbr_original_d.png'))
mat=bpy.data.materials.new('Decoded original cloth');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
floor_mat=bpy.data.materials.new('Ground');floor_mat.use_nodes=True;bs=floor_mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.10,.10,.10,1);bs.inputs['Roughness'].default_value=1
bpy.ops.mesh.primitive_plane_add(size=4,location=(0,0,0));ground=bpy.context.object;ground.data.materials.append(floor_mat)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.render.resolution_x=1100;s.render.resolution_y=650;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.world=bpy.data.worlds.new('Shoe review');s.world.color=(.20,.20,.20)
bpy.ops.object.light_add(type='AREA',location=(0,0,3));bpy.context.object.data.energy=500;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=3
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=.42;s.camera=cam
centers={}
for sign in [-1,1]:
    points=[]
    for folder in [ROOT/'build/baseline_v1.0.1/export',ROOT/'build/final_export']:
        for file in (folder/'geo').glob('*.bin'):
            for m in read_geo(file):
                if m['name'].split('.b')[0] in names and m['pos'][:,0].mean()*sign>0:points.append(lbs(m['pos'],m['bi'],m['bw'],skin))
    points=np.concatenate(points);center=(points.min(0)+points.max(0))/2;center[2]=.085;centers[sign]=Vector(center)
for label,folder in [('before',ROOT/'build/baseline_v1.0.1/export'),('after',ROOT/'build/final_export')]:
    for sign,side in [(-1,'left'),(1,'right')]:
        objects=[]
        for file in (folder/'geo').glob('*.bin'):
            for m in read_geo(file):
                if m['name'].split('.b')[0] not in names or m['pos'][:,0].mean()*sign<=0:continue
                p=lbs(m['pos'],m['bi'],m['bw'],skin);mesh=bpy.data.meshes.new(m['name']);mesh.from_pydata(p.tolist(),[],m['idx'].reshape(-1,3).tolist());mesh.update();uv=mesh.uv_layers.new(name='UVMap');coords=m['uv'].copy();coords[:,1]=1-coords[:,1]
                for loop in mesh.loops:uv.data[loop.index].uv=coords[loop.vertex_index]
                obj=bpy.data.objects.new(m['name'],mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat);objects.append(obj)
        assert objects
        center=centers[sign];cam.location=center+Vector((sign*4,0,.22));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        s.render.filepath=str(ROOT/'reports'/f'shoe_{label}_{side}.png');bpy.ops.render.render(write_still=True)
        for obj in objects:bpy.data.objects.remove(obj,do_unlink=True)
print('FINAL_SHOE_PREVIEWS_READY')
