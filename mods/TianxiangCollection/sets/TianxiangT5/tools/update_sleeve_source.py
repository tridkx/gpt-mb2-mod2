"""Apply the final sleeve recipe to the accepted source without rebuilding anatomy."""
import bpy, json, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
config=json.loads((ROOT/'tools/sleeve_config.json').read_text())
recipe=json.loads((ROOT/'build/sleeve_recipe.json').read_text())
baseline=json.loads((ROOT/'build/sleeve_baseline/meshes.json').read_text())
m=next(m for m in baseline if m['name']=='tx5_body_00')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'build/sleeve_baseline/TianxiangT5_Rigged.blend'))
obj=bpy.data.objects['tx5_body_00']
attr=obj.data.color_attributes['ClothDistance']
points=np.array(m['pos'])
maximum_match_error=0.0
for v in obj.data.vertices:
    nearest=int(np.argmin(np.linalg.norm(points-np.array(v.co),axis=1)))
    error=float(np.linalg.norm(points[nearest]-np.array(v.co)))
    assert error<2e-6, (v.index,error)
    maximum_match_error=max(maximum_match_error,error)
    attr.data[v.index].color=(1,1,1,recipe['meshes'][m['name']]['alpha'][nearest]/255.0)
obj['cloth_distance_multiplier']=config['distance_multiplier']
obj['cloth_max_distance']=max(recipe['meshes'][m['name']]['alpha'])/255*config['distance_multiplier']
obj['cloth_material']=config['material']['Name']
obj['cloth_lods']='LOD0, LOD1'
obj['cloth_recipe']='tools/sleeve_config.json'
preview=bpy.data.objects.get('tx5_body_00_cloth_preview')
if preview:
    for v in preview.data.vertices:
        preview.data.color_attributes['ClothDistance'].data[v.index].color=attr.data[v.index].color
        pin=preview.vertex_groups.get('ClothPin')
        if pin:pin.add([v.index],1.0 if attr.data[v.index].color[3]==0 else 0.0,'REPLACE')
    # This optional Blender preview remains hidden and is not a runtime solver.
    preview['game_cloth_recipe']=obj['cloth_recipe']
for img in bpy.data.images:
    if img.source=='FILE':
        path=ROOT/'tex'/Path(img.filepath.replace('\\','/')).name
        if path.exists():
            img.filepath=str(path);img.reload();img.pack()
            img.filepath='//../tex/'+path.name
        assert img.packed_file is not None, img.name
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith('_cloth_preview')]
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/TianxiangT5_Rigged.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/TianxiangT5_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',colors_type='LINEAR',use_mesh_modifiers=False)
print('SLEEVE_SOURCE_READY')
