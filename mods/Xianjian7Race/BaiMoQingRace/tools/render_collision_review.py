import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
"""Render actual final-package geometry, decoded diffuse and byte-quantized skin."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=workspace_root(ROOT)
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'));sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
lod=int(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else 0
folder=ROOT/('build/final_export_lod'+str(lod));meshes=[m for f in (folder/'geo').glob('*.bin') for m in read_geo(f) if not m['name'].startswith('bmq_hidden')]
materialinfo=json.loads((ROOT/'reports/material_names.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True)
materials={}
for name,rec in materialinfo.items():
    mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
    image=bpy.data.images.load(str(ROOT/'build/final_export_lod0/tex'/(rec['textures']['0']+'.png')),check_existing=True);tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if rec['template']=='alpha':mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
    # Weak emission preserves the original diffuse colors under neutral studio light.
    mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.15
    materials[name]=mat
objects=[]
for m in meshes:
    me=bpy.data.meshes.new(m['name']);me.from_pydata(m['pos'].tolist(),[],m['idx'].reshape(-1,3).tolist());me.update();uv=me.uv_layers.new(name='UVMap');u=m['uv'].copy();u[:,1]=1-u[:,1]
    for loop in me.loops:uv.data[loop.index].uv=u[loop.vertex_index]
    for face in me.polygons:face.use_smooth=True
    o=bpy.data.objects.new(m['name'],me);bpy.context.collection.objects.link(o);me.materials.append(materials[m['material']]);objects.append(o)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.render.resolution_x=900;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard'
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1)
lights=[]
for offset,energy,size in [((2,3,4),300,4),((-2,2,2),180,3),((0,-3,3),220,3)]:
    bpy.ops.object.light_add(type='AREA');light=bpy.context.object;light.data.energy=energy;light.data.size=size;lights.append((light,Vector(offset)))
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam
def render(label,offset,close=False):
    points=np.concatenate(base);center=Vector((points.min(0)+points.max(0))/2)
    if close:center.z=float(points[:,2].max()-.2)
    cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.6 if close else max(1.9,float(np.ptp(points[:,2]))*1.12)
    for light,loc in lights:light.location=center+loc;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(ROOT/'reports'/('collision_proxy_'+(('lod'+str(lod)+'_') if lod else '')+label+'.png'));bpy.ops.render.render(write_still=True)
rig=parse_skeljson(json.loads((ROOT/'reports/final_skeleton.json').read_text()));anim=parse_animjson(json.loads((ROOT/'reports/ui_neutral_female.json').read_text()));skin=skin_matrices(rig,anim,max(1,anim['start']))
base=[lbs(m['pos'],m['bi'],m['bw'],skin) for m in meshes]
for phase in ['before','after']:
 for o,m,p in zip(objects,meshes,base):
  file=ROOT/'build'/(m['name']+'_settled_comparison.npz');q=np.load(file)[phase] if file.exists() else p
  assert len(q)==len(p),(m['name'],len(q),len(p))
  o.data.vertices.foreach_set('co',q.astype('f4').ravel());o.data.update()
 render(phase+'_front',(0,4,0));render(phase+'_side',(4,0,0))
print('CPU_PROXY_PREVIEWS_READY')
