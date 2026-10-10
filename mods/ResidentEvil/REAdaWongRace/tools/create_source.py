"""Create editable native-rig Blend/FBX and source previews."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[2]
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rig=parse_skeljson(json.loads((ROOT/'build/bind_skeleton.json').read_text()))
manifest=json.loads((ROOT/'build/manifest.json').read_text());arrays=np.load(ROOT/'build/fitted_model.npz')
materials=json.loads((ROOT/'tex/materials.json').read_text()) if (ROOT/'tex/materials.json').exists() else {}
diffuse={};current=''
for line in (ROOT/'input/cha200/Ada_cha200_MainStory_full.mtl').read_text().splitlines():
    if line.startswith('newmtl '):current=line.split()[1]
    elif line.startswith('map_Kd '):diffuse[current]=Path(line.split()[1]).name
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name='adar_skeleton'
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
        material=bpy.data.materials.new('adar_'+rec['material'].lower());material.use_nodes=True
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
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/REAdaWongRace_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True,use_mesh_modifiers=False)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/REAdaWongRace_Rigged.blend'))

print('SOURCE_READY')
