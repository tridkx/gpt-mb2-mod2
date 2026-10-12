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
argument=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '0'
arm_only=argument=='arm';lod=0 if arm_only else int(argument)
folder=ROOT/('build/final_export_lod'+str(lod));meshes=[m for f in (folder/'geo').glob('*.bin') for m in read_geo(f) if not m['name'].startswith('txgirl1_hidden')]
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
    points=np.concatenate([np.array([v.co for v in o.data.vertices]) for o in objects]);center=Vector((points.min(0)+points.max(0))/2)
    if close:center.z=float(points[:,2].max()-.2)
    cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.6 if close else max(1.9,float(np.ptp(points[:,2]))*1.12)
    for light,loc in lights:light.location=center+loc;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(ROOT/'reports'/('final_'+(('lod'+str(lod)+'_') if lod else '')+label+'.png'));bpy.ops.render.render(write_still=True)
if arm_only:
    for path in sorted((ROOT/'build').glob('arm_*_?.npz')):
        values=np.load(path)
        for o,m in zip(objects,meshes):o.data.vertices.foreach_set('co',values[m['name']].astype('f4').ravel());o.data.update()
        render(path.stem+'_front',(0,4,0));render(path.stem+'_side',(4,0,0))
    print('CAPTURED_ARM_COMPARISONS_READY');sys.exit(0)
render('rest_front',(0,4,0));render('rest_back',(0,-4,0));render('rest_side',(4,0,0));render('head',(0,4,0),True)
if lod:
    print('LOD_PREVIEWS_READY',lod);sys.exit(0)
rig=parse_skeljson(json.loads((ROOT/'reports/final_skeleton.json').read_text()));report=json.loads((ROOT/'reports/release_validation.json').read_text());previews=[]
for motion in report['motions']:
    label=motion['label'];anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));frame=motion['worst_frame'];skin=skin_matrices(rig,anim,frame)
    for o,m in zip(objects,meshes):p=lbs(m['pos'],m['bi'],m['bw'],skin);o.data.vertices.foreach_set('co',p.astype('f4').ravel());o.data.update()
    render(label+'_worst',(2.5,4,0));render(label+'_side',(4,0,0))
    if label.startswith(('stand_','ui_neutral_')):render(label+'_front',(0,4,0))
    previews.append({'label':label,'frame':frame,'file':'reports/final_'+label+'_worst.png'})
(ROOT/'reports/final_preview_manifest.json').write_text(json.dumps({'package_sha256':report['final_package_sha256'],'source':'Final TPAC re-export, decoded diffuse and byte weights','game_cloth_solver_used':False,'previews':previews},indent=2))
print('FINAL_PREVIEWS_READY')
