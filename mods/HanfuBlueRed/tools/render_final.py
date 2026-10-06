"""Preview the final TPAC re-export, with native animation and quantized skin."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'D:\gpt-mb2-mod\tools');sys.path.insert(0,r'D:\gpt-mb2-mod\previewer')
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
bpy.ops.wm.read_factory_settings(use_empty=True)
meshes=[m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f)]
assert meshes and all(m['lod']==0 for m in meshes)
image_path=next((ROOT/'build/final_export').rglob('hbr_original_d*.png'))
image=bpy.data.images.load(str(image_path));mat=bpy.data.materials.new('Final decoded 4K');mat.use_nodes=True;mat.node_tree.nodes.clear()
out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');em=mat.node_tree.nodes.new('ShaderNodeEmission');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
objects=[]
for m in meshes:
    mesh=bpy.data.meshes.new(m['name']);mesh.from_pydata(m['pos'].tolist(),[],m['idx'].reshape(-1,3).tolist());mesh.update()
    uv=mesh.uv_layers.new(name='UVMap');coords=m['uv'].copy();coords[:,1]=1-coords[:,1]
    for loop in mesh.loops:uv.data[loop.index].uv=coords[loop.vertex_index]
    obj=bpy.data.objects.new(m['name'],mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat);objects.append(obj)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.render.resolution_x=1000;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Review');s.world.color=(.16,.16,.16);s.view_settings.view_transform='Standard'
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam
def render(name,offset):
    points=np.concatenate([np.array([v.co for v in o.data.vertices]) for o in objects]);center=Vector((points.min(0)+points.max(0))/2)
    cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(1.9,float(np.ptp(points[:,2]))*1.15)
    s.render.filepath=str(ROOT/'reports'/(name+'.png'));bpy.ops.render.render(write_still=True)
render('final_rest_front',(0,4,0));render('final_rest_back',(0,-4,0));render('final_rest_side',(4,0,0))
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
report=json.loads((ROOT/'reports/release_validation.json').read_text());previews=[]
for motion in report['motions']:
    label=motion['label'];frame=motion['worst_frame'];anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));skin=skin_matrices(rig,anim,frame)
    for obj,m in zip(objects,meshes):
        posed=lbs(m['pos'],m['bi'],m['bw'],skin);obj.data.vertices.foreach_set('co',posed.astype('f4').ravel());obj.data.update()
    render('final_'+label+'_worst',(2.6,4,0));previews.append({'label':label,'frame':frame,'path':'reports/final_'+label+'_worst.png'})
(ROOT/'reports/final_preview_manifest.json').write_text(json.dumps({'package_sha256':report['final_package_sha256'],'source':'Final TPAC re-export LOD0 with decoded texture and byte weights','game_cloth_solver_used':False,'motion_previews':previews},indent=2))
print('FINAL_PREVIEWS_READY')
