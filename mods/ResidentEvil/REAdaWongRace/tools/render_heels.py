"""Same-camera heel close-ups from the old and final TPAC exports."""
from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[2]
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'))
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
frame=169;anim=parse_animjson(json.loads((ROOT/'reports/idle.json').read_text()))
baseline=ROOT/'build/baseline_v0.1.0'
versions=[('before',baseline/'export',baseline/'final_skeleton.json'),('after',ROOT/'build/final_export_lod0',ROOT/'reports/final_skeleton.json')]
rows=[]
for label,folder,rigpath in versions:
    rig=parse_skeljson(json.loads(rigpath.read_text()));skin=skin_matrices(rig,anim,frame);pieces=[]
    for f in (folder/'geo').glob('*.bin'):
        for m in read_geo(f):
            if not m['name'].startswith('adar_legs_boots'):continue
            tri=m['idx'].reshape(-1,3)
            keep=((m['pos'][tri,:,][...,0]>0)&(m['pos'][tri,:,][...,2]<.29)).all(1)
            tri=tri[keep]
            if len(tri):pieces.append((m,lbs(m['pos'],m['bi'],m['bw'],skin),tri))
    rows.append((label,pieces))
points=np.concatenate([p[np.unique(tri)] for label,pieces in rows for m,p,tri in pieces]);center=Vector((points.min(0)+points.max(0))/2)
materialinfo=json.loads((ROOT/'reports/material_names.json').read_text())
for label,pieces in rows:
    bpy.ops.wm.read_factory_settings(use_empty=True);materials={}
    for m,p,tri in pieces:
        name=m['material']
        if name not in materials:
            mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'build/final_export_lod0/tex'/(materialinfo[name]['textures']['0']+'.png')),check_existing=True)
            mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);materials[name]=mat
        me=bpy.data.meshes.new(m['name']);me.from_pydata(p.tolist(),[],tri.tolist());me.update();uv=me.uv_layers.new(name='UVMap');u=m['uv'].copy();u[:,1]=1-u[:,1]
        for loop in me.loops:uv.data[loop.index].uv=u[loop.vertex_index]
        for face in me.polygons:face.use_smooth=True
        o=bpy.data.objects.new(m['name'],me);bpy.context.collection.objects.link(o);me.materials.append(materials[name])
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=900;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard'
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1)
    for delta,power in [((2,2,3),250),((-2,0,1),120)]:
        bpy.ops.object.light_add(type='AREA');o=bpy.context.object;o.location=center+Vector(delta);o.data.energy=power;o.data.size=3;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.location=center+Vector((3,.2,.05));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.38;scene.camera=cam
    scene.render.filepath=str(ROOT/'reports'/('heel_'+label+'.png'));bpy.ops.render.render(write_still=True)
report=json.loads((ROOT/'reports/heel_validation.json').read_text())
(ROOT/'reports/heel_preview_manifest.json').write_text(json.dumps({'version':report['version'],'frame':frame,'source':'Actual TPAC data, same camera and native inventory idle frame','before_package_sha256':report['baseline_package_sha256'],'after_package_sha256':report['final_package_sha256']},indent=2))
