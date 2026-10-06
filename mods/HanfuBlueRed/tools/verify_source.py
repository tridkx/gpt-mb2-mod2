import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.blend'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert len(meshes)==23 and len(rigs)==1 and len(rigs[0].data.bones)==28
referenced={n.image for o in meshes for m in o.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
assert len(referenced)==1
assert all(i.packed_file and tuple(i.size)==(4096,4096) for i in referenced)
for o in meshes:
    assert o.data.uv_layers and len(o.vertex_groups)==28
    assert any(m.type=='ARMATURE' and m.object==rigs[0] for m in o.modifiers)
blend={'meshes':len(meshes),'native_bones':28,'referenced_textures':1,'packed_texture_resolution':[4096,4096]}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.fbx'),use_anim=False)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert len(meshes)==23 and len(rigs)==1 and len(rigs[0].data.bones)==28
images={n.image for o in meshes for m in o.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
assert images and all(tuple(i.size)==(4096,4096) for i in images)
hashes={name:hashlib.sha256((ROOT/'source'/name).read_bytes()).hexdigest() for name in ['HanfuBlueRed_Rigged.blend','HanfuBlueRed_Rigged.fbx']}
(ROOT/'reports/source_validation.json').write_text(json.dumps({'status':'pass','blend':blend,'fbx_meshes':len(meshes),'fbx_bones':28,'sha256':hashes},indent=2))
print('EDITABLE_SOURCE_VALIDATED')
