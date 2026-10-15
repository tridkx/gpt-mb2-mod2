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
folder=ROOT/('build/final_export_lod'+str(lod));meshes=[m for f in (folder/'geo').glob('*.bin') for m in read_geo(f) if m['name'].startswith('emilie_part_') or m['name']=='emilie_cloth_proxy']
materialinfo=json.loads((ROOT/'reports/material_names.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True)
materials={};fully_discarded=set()
for name,rec in materialinfo.items():
    mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
    image=bpy.data.images.load(str(ROOT/'build/final_export_lod0/tex'/(rec['textures']['0']+'.png')),check_existing=True);tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if rec['template']=='alpha' or rec.get('blendMode')=='factor':mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
    # Match complete GPU alpha-test discard. Co-planar transparent geometry in
    # Cycles can still perturb ray offsets; discard only after decoded-alpha proof.
    if rec['template']=='alpha' and 'alpha_test' in rec.get('shaderMaterialFlags',[]):
        pixels=np.empty(image.size[0]*image.size[1]*4,dtype='f4');image.pixels.foreach_get(pixels)
        if pixels.reshape(-1,4)[:,3].max()<rec.get('alphaTest',.25):fully_discarded.add(name)
    # Weak emission preserves the original diffuse colors under neutral studio light.
    mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.15
    materials[name]=mat
objects=[]
for m in meshes:
    me=bpy.data.meshes.new(m['name']);me.from_pydata(m['pos'].tolist(),[],m['idx'].reshape(-1,3).tolist());me.update();uv=me.uv_layers.new(name='UVMap');u=m['uv'].copy();u[:,1]=1-u[:,1]
    for loop in me.loops:uv.data[loop.index].uv=u[loop.vertex_index]
    for face in me.polygons:face.use_smooth=True
    o=bpy.data.objects.new(m['name'],me);bpy.context.collection.objects.link(o);me.materials.append(materials[m['material']]);objects.append(o)
    if m['material'] in fully_discarded:o.hide_render=True;o['reason']='All decoded texels below material alpha-test threshold'
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=6;s.render.resolution_x=720;s.render.resolution_y=920;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard'
s.view_settings.exposure=-.65
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
if '--cpu-cloth' in sys.argv:
    sys.path.insert(0,str(WORKSPACE/'tools/cloth_compiler'))
    from mapping_payload import read as read_map,reconstruct
    diagnostic=json.loads((ROOT/'reports/cloth_diagnostics.json').read_text());items=json.loads((ROOT/'build/mapped_final/inspection.json').read_text());body=next(m for m in items if m['Name']=='emilie_body');byguid={s['OwnerGuid']:s for s in body['segments']};guidbyname={m['Name']:m['Guid'] for m in body['meshes']};rig=parse_skeljson(json.loads((ROOT/'reports/final_skeleton.json').read_text()));preview_rows=[]
    alpha_by_guid={}
    for path in (ROOT/'build/mapped_render_input').glob('*.mesh.json'):
        row=json.loads(path.read_text());alpha_by_guid[row['guid']]=np.array(row['alpha'])
    for case in diagnostic['results']:
        if case.get('metamesh')!='emilie_cloth_proxy' or 'report' not in case:continue
        path=ROOT/case['report'];rr=json.loads(path.read_text());frames=np.load(path.parent/'frames.npz');label=case['motion'];frame=int(rr['worst_stretch_frame']);source_frame=int(rr['frame_metrics'][frame].get('source_frame',frame+1));anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));skin=skin_matrices(rig,anim,source_frame);points=frames['positions'][frame];triangles=frames['triangles'];normals=np.zeros_like(points);tri=points[triangles];fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);np.add.at(normals,triangles.ravel(),np.repeat(fn,3,axis=0));bad=np.linalg.norm(normals,axis=1)<1e-8;normals[bad]=[0,1,0];normals/=np.linalg.norm(normals,axis=1)[:,None]
        for o,m in zip(objects,meshes):
            p=lbs(m['pos'],m['bi'],m['bw'],skin)
            if m['name'] in guidbyname and guidbyname[m['name']] in byguid:
                guid=guidbyname[m['name']];indices,weights=read_map(Path(byguid[guid]['path']).read_bytes());active=alpha_by_guid[guid]>0;p[active]=reconstruct(points,normals,indices[active],weights[active])
            o.data.vertices.foreach_set('co',p.astype('f4').ravel());o.data.update()
        render('cpu_cloth_'+label,(2.5,4,0));render('cpu_cloth_'+label+'_back',(0,-4,0));preview_rows.append({'motion':label,'simulation_frame':frame,'source_frame':source_frame,'game_solver_used':False,'normal_reconstruction':'Deformed proxy triangle normals; approximate'})
    (ROOT/'reports/cpu_mapping_preview.json').write_text(json.dumps({'status':'review_required','scope':'Visual reconstruction from final mapping bytes and approximate CPU proxy trajectory','game_verified':False,'previews':preview_rows},indent=2));sys.exit(0)
render('rest_front',(0,4,0));render('rest_back',(0,-4,0));render('rest_side',(4,0,0));render('head',(0,4,0),True)
if lod or '--rest' in sys.argv:
    print('LOD_PREVIEWS_READY',lod);sys.exit(0)
rig=parse_skeljson(json.loads((ROOT/'reports/final_skeleton.json').read_text()));report=json.loads((ROOT/'reports/release_validation.json').read_text()) if (ROOT/'reports/release_validation.json').exists() else {'motions':json.loads((ROOT/'reports/motion_failure.json').read_text()),'final_package_sha256':'unreleased_candidate'};previews=[]
for motion in report['motions']:
    if '--review' in sys.argv and motion['label'] not in ['facegen','run','bow','riding']:continue
    label=motion['label'];anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));frame=motion['worst_frame'];skin=skin_matrices(rig,anim,frame)
    for o,m in zip(objects,meshes):p=lbs(m['pos'],m['bi'],m['bw'],skin);o.data.vertices.foreach_set('co',p.astype('f4').ravel());o.data.update()
    render(label+'_worst',(2.5,4,0));render(label+'_side',(4,0,0));previews.append({'label':label,'frame':frame,'file':'reports/final_'+label+'_worst.png'})
(ROOT/'reports/final_preview_manifest.json').write_text(json.dumps({'package_sha256':report['final_package_sha256'],'source':'Final TPAC re-export, decoded diffuse and byte weights','game_cloth_solver_used':False,'previews':previews},indent=2))
print('FINAL_PREVIEWS_READY')
