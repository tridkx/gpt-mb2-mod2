"""Save render and simulation sources matching the offline-authored package."""
import bpy,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
recipe=json.loads((ROOT/'build/mapped/recipe.json').read_text())
meshes={m['name']:m for m in json.loads((ROOT/'build/sleeve_final.json').read_text())}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'build/mapped_baseline/TianxiangT5_Rigged.blend'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for name in ['tx5_body_00']:
    obj=bpy.data.objects[name];p=np.array(meshes[name]['pos']);a=recipe['mapped'][name]['alpha']
    color=obj.data.color_attributes['ClothDistance']
    for v in obj.data.vertices:
        i=int(np.argmin(np.linalg.norm(p-np.array(v.co),axis=1)))
        assert np.linalg.norm(p[i]-v.co)<2e-6
        color.data[v.index].color=(1,1,1,a[i]/255)
    obj['cloth_route']='Mapped simulation; baked b97e0f10 constraints and af41613e mapping'
    obj['cloth_simulation_mesh']=recipe['name']
    obj['cloth_material']=recipe['material']['Name']
    obj['cloth_lods']='LOD0, LOD1, LOD2, LOD3'
    obj['cloth_recipe']='tools/build_mapped_sleeves.ps1'
for img in bpy.data.images:
    if img.source=='FILE':assert img.packed_file is not None,img.name
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith('_cloth_preview')]
for name in recipe.get('disabled_render_meshes',[]):
    bpy.data.objects[name]['cloth_route']='Skinning only; disabled after runtime stretching'
    bpy.data.objects[name]['cloth_enabled']=False

def export(path,selected):
    bpy.ops.object.select_all(action='DESELECT')
    for o in [rig]+selected:o.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','ARMATURE'},
        add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
        mesh_smooth_type='FACE',colors_type='LINEAR',use_mesh_modifiers=False)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/TianxiangT5_Rigged.blend'))
export(ROOT/'source/TianxiangT5_Rigged.fbx',objects)
vertices=[];groups=[];uv=[]
for ref in recipe['sources']:
    m=meshes[ref['mesh']];i=ref['index'];point=np.array(m['pos'][i]);obj=bpy.data.objects[ref['mesh']]
    j=int(np.argmin([np.linalg.norm(point-v.co) for v in obj.data.vertices]))
    assert np.linalg.norm(point-obj.data.vertices[j].co)<2e-6
    vertices.append(point.tolist());groups.append([(obj.vertex_groups[g.group].name,g.weight) for g in obj.data.vertices[j].groups]);uv.append(m['uv'][i])
mesh=bpy.data.meshes.new(recipe['name']);faces=np.array(recipe['faces']).reshape(-1,3)
mesh.from_pydata(vertices,[],faces.tolist());mesh.update()
proxy=bpy.data.objects.new(recipe['name'],mesh);bpy.context.scene.collection.objects.link(proxy)
for group in bpy.data.objects['tx5_body_00'].vertex_groups:proxy.vertex_groups.new(name=group.name)
for i,weights in enumerate(groups):
    for name,weight in weights:proxy.vertex_groups[name].add([i],weight,'REPLACE')
color=mesh.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
for i,a in enumerate(recipe['alpha']):color.data[i].color=(1,1,1,a/255)
mesh.color_attributes.active_color=color
uvlayer=mesh.uv_layers.new(name='UVMap')
for loop in mesh.loops:uvlayer.data[loop.index].uv=uv[loop.vertex_index]
mod=proxy.modifiers.new('Native skeleton','ARMATURE');mod.object=rig
proxy['cloth_distance_multiplier']=recipe['multiplier'];proxy['cloth_material']=recipe['material']['Name']
proxy['cooked_generation']='tools/build_mapped_recipe.py'
proxy['note']='Sleeve-only simulation proxy. Skirt remains on accepted skinning and is excluded from cloth mapping.'
for obj in list(bpy.context.scene.objects):
    if obj not in [rig,proxy]:bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/TianxiangT5_ClothSimulation.blend'))
export(ROOT/'source/TianxiangT5_ClothSimulation.fbx',[proxy])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangT5_ClothSimulation.blend'))
assert len(bpy.data.objects[recipe['name']].data.vertices)==len(vertices)
assert sum(img.source=='FILE' and img.packed_file is not None for img in bpy.data.images)==23
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'source/TianxiangT5_ClothSimulation.fbx'))
imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==1
assert len(imported[0].data.vertices)==len(vertices)
assert all(len(v.groups)>0 for v in imported[0].data.vertices)
assert imported[0].data.color_attributes.active_color is not None
print('MAPPED_SOURCE_VALIDATED',len(vertices),'simulation vertices')
