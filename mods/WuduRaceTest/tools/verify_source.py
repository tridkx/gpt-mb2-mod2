"""Reopen editable sources and check geometry and embedded textures."""
import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
expected=np.load(R/'build/source_positions.npz')
hand_frames=np.load(R/'build/hand_source_shapes.npz')['frames']
def verify_hand_keys():
    ob=bpy.data.objects['wdr_part_04'];keys=ob.data.shape_keys.key_blocks;assert len(keys)==27
    error=0
    for index,expected_frame in enumerate(hand_frames):
        points=np.array([ob.matrix_world@v.co for v in keys[index+1].data]);error=max(error,float(abs(points-expected_frame).max()))
    assert error<1e-5
    return error
bpy.ops.wm.open_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
manifest=json.loads((R/'build/rig_manifest.json').read_text());max_error=0
for row in manifest:
    ob=bpy.data.objects[row['object']];p=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);err=float(abs(p-expected[ob.name+'_p']).max());max_error=max(max_error,err);assert err<1e-6
    assert len(ob.vertex_groups)==28 and len(ob.data.uv_layers)>0
    for v in ob.data.vertices:assert 1<=len(v.groups)<=4 and abs(sum(g.weight for g in v.groups)-1)<1e-5
assert all(im.packed_file is not None for im in bpy.data.images if im.source=='FILE')
blend_images=sum(1 for im in bpy.data.images if im.source=='FILE')
blend_hand_error=verify_hand_keys()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'source/WuduCanglan_Rigged.fbx'),use_anim=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)==13
armatures=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(armatures)==1 and len(armatures[0].data.bones)==28
for ob in meshes:
    p=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);err=float(abs(p-expected[ob.name+'_p']).max());max_error=max(max_error,err);assert err<1e-5
fbx_hand_error=verify_hand_keys()
(R/'reports/editable_source_validation.json').write_text(json.dumps(dict(status='pass',blend_reopened=True,fbx_reopened=True,packed_images=blend_images,max_vertex_error_m=max_error,hand_morph_channels=26,blend_hand_morph_error_m=blend_hand_error,fbx_hand_morph_error_m=fbx_hand_error),indent=2))
print('EDITABLE_SOURCES_VERIFIED',max_error)
