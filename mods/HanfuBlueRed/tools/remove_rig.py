"""Export a static, unrigged Tripo input without changing the original input."""
import bpy
import json
import hashlib
from pathlib import Path
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'input/tripo_convert_1e91e0a9-4975-4e4d-b3a7-f926592b992a.fbx'
OUTPUT = ROOT / 'source/HanfuBlueRed_NoRig.fbx'
ORIGINAL = Path('D:/dsh-tripo/汉服少女蓝红配色') / INPUT.name

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot():
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert len(meshes) == 1
    obj = meshes[0]
    mesh = obj.data
    mesh.calc_loop_triangles()
    return obj, {
        'vertices': len(mesh.vertices),
        'triangles': len(mesh.loop_triangles),
        'uv_layers': [u.name for u in mesh.uv_layers],
        'materials': [m.name for m in mesh.materials],
    }, [obj.matrix_world @ v.co for v in mesh.vertices]

original_hash = sha(ORIGINAL)
assert sha(INPUT) == original_hash
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(INPUT), use_anim=False)
obj, before, points = snapshot()
uv_before = [tuple(x.uv) for x in obj.data.uv_layers.active.data]
for modifier in list(obj.modifiers):
    if modifier.type == 'ARMATURE':
        obj.modifiers.remove(modifier)
world = obj.matrix_world.copy()
obj.parent = None
obj.matrix_world = world
obj.vertex_groups.clear()
obj.animation_data_clear()
obj.data.animation_data_clear()
for armature in list(bpy.data.objects):
    if armature.type == 'ARMATURE':
        bpy.data.objects.remove(armature, do_unlink=True)
for armature in list(bpy.data.armatures):
    bpy.data.armatures.remove(armature)
for action in list(bpy.data.actions):
    bpy.data.actions.remove(action)
for image in bpy.data.images:
    if image.source == 'FILE':
        image.filepath = str(ROOT / 'tex/汉服女孩3d模型_basecolor.JPEG')
        image.reload()
        assert tuple(image.size) == (4096, 4096)
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.fbx(
    filepath=str(OUTPUT), use_selection=True, object_types={'MESH'},
    use_mesh_modifiers=False, add_leaf_bones=False, bake_anim=False,
    path_mode='COPY', embed_textures=True,
)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(OUTPUT), use_anim=False)
obj, after, result_points = snapshot()
assert before == after, (before, after)
assert not any(o.type == 'ARMATURE' for o in bpy.data.objects)
assert len(bpy.data.armatures) == 0
assert len(obj.vertex_groups) == 0
assert not any(m.type == 'ARMATURE' for m in obj.modifiers)
assert not bpy.data.actions
tree = KDTree(len(points))
for i, p in enumerate(points):
    tree.insert(p, i)
tree.balance()
max_error = max(tree.find(p)[2] for p in result_points)
assert max_error < 0.00001, max_error
uv_after = [tuple(x.uv) for x in obj.data.uv_layers.active.data]
assert len(uv_before) == len(uv_after)
uv_error = max(abs(a-b) for u,v in zip(uv_before,uv_after) for a,b in zip(u,v))
assert uv_error < 0.00001, uv_error
images = [im for im in bpy.data.images if im.source == 'FILE']
assert images and all(tuple(im.size) == (4096, 4096) for im in images)
assert sha(ORIGINAL) == original_hash
report = {
    'input_sha256': original_hash, 'output_sha256': sha(OUTPUT),
    'before': before, 'after': after, 'armatures': 0, 'vertex_groups': 0,
    'max_position_error': max_error, 'max_uv_error': uv_error,
    'texture_size': [4096,4096], 'source_unchanged': True,
    'output': str(OUTPUT),
}
(ROOT / 'reports/remove_rig.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
