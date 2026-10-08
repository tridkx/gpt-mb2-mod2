"""Create editable native-rig Blend/FBX and source previews."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[2]
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
manifest=json.loads((ROOT/'build/manifest.json').read_text());arrays=np.load(ROOT/'build/fitted_model.npz')
materials=json.loads((ROOT/'tex/materials.json').read_text()) if (ROOT/'tex/materials.json').exists() else {}
diffuse={};current=''
for line in (ROOT/'input/cha200/Ada_cha200_MainStory_full.mtl').read_text().splitlines():
    if line.startswith('newmtl '):current=line.split()[1]
    elif line.startswith('map_Kd '):diffuse[current]=Path(line.split()[1]).name
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name='human_skeleton'
bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0])
bone_names=[name+'_'+str(i) for i,name in enumerate(rig['names'])]
for i,name in enumerate(bone_names):
    b=arm.data.edit_bones.new(name);b.matrix=Matrix(rig['restWorld'][i].tolist());b.length=.05
for i,name in enumerate(bone_names):
    if rig['parent'][i]>=0:arm.data.edit_bones[name].parent=arm.data.edit_bones[bone_names[rig['parent'][i]]]
bpy.ops.object.mode_set(mode='OBJECT');arm.show_in_front=True
objects=[];cache={}
for rec in manifest:
    name=rec['object'];p=arrays[name+'_p'];f=arrays[name+'_f'];n=arrays[name+'_n'];uv=arrays[name+'_uv'];w=arrays[name+'_w']
    me=bpy.data.meshes.new(name);me.from_pydata(p.tolist(),[],f.tolist());me.update()
    layer=me.uv_layers.new(name='UVMap')
    for loop in me.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
    for face in me.polygons:face.use_smooth=True
    me.normals_split_custom_set_from_vertices(n.tolist())
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    for i,bone in enumerate(bone_names):
        group=o.vertex_groups.new(name=bone)
        for v in np.flatnonzero(w[:,i]>1e-7):group.add([int(v)],float(w[v,i]),'REPLACE')
    mod=o.modifiers.new('Native human skin','ARMATURE');mod.object=arm;o.parent=arm
    if rec['material'] not in cache:
        material=bpy.data.materials.new('reada_'+rec['material'].lower());material.use_nodes=True
        bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.5
        info=materials.get(rec['material'],{})
        path=ROOT/'tex'/info.get('diffuse',diffuse[rec['material']])
        if not path.exists():path=ROOT/'input/exported_textures'/diffuse[rec['material']]
        im=bpy.data.images.load(str(path),check_existing=True);im.pack()
        tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;material.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        if info.get('cutout'):
            material.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);material.surface_render_method='DITHERED'
        if info.get('normal'):
            image=bpy.data.images.load(str(ROOT/'tex'/info['normal']),check_existing=True);image.colorspace_settings.name='Non-Color';image.pack()
            t=material.node_tree.nodes.new('ShaderNodeTexImage');t.image=image;nm=material.node_tree.nodes.new('ShaderNodeNormalMap');material.node_tree.links.new(t.outputs['Color'],nm.inputs['Color']);material.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        cache[rec['material']]=material
    me.materials.append(cache[rec['material']]);objects.append(o)
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/REAdaWongDefault_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True,use_mesh_modifiers=False)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/REAdaWongDefault_Rigged.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.render.resolution_x=900;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard'
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1)
for loc,energy,size in [((2,3,4),650,4),((-2,2,2),350,3),((0,-3,3),450,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2;s.camera=cam
def render(label,offset):
    center=Vector((0,0,.9));cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/'reports'/('source_'+label+'.png'));bpy.ops.render.render(write_still=True)
render('rest_front',(0,4,0));render('rest_side',(4,0,0))
for label in ['idle','run','bow','riding']:
    path=ROOT/'reports'/(label+'.json')
    if not path.exists():continue
    anim=parse_animjson(json.loads(path.read_text()));frame=max(anim['start'],min(8,anim['frames']-1));skin=skin_matrices(rig,anim,frame)
    for o,rec in zip(objects,manifest):
        name=rec['object'];w=arrays[name+'_w'];bi=np.argsort(-w,axis=1)[:,:4];weights=np.take_along_axis(w,bi,axis=1);q=np.floor(weights*255).astype('u1');q[:,0]+=255-q.sum(1).astype('u1')
        for mod in list(o.modifiers):o.modifiers.remove(mod)
        posed=lbs(arrays[name+'_p'],bi,q,skin);o.data.vertices.foreach_set('co',posed.astype('f4').ravel());o.data.update()
    render(label,(2.5,4,0))
print('SOURCE_READY')
