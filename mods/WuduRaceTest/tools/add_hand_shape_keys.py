"""Store the same 26 hand channels in the editable Blend and FBX."""
import bpy,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
hand=bpy.data.objects['wdr_part_04'];hand.shape_key_clear();hand.shape_key_add(name='Basis')
frames=np.load(R/'build/hand_source_shapes.npz')['frames']
for index,points in enumerate(frames):
    key=hand.shape_key_add(name=f'hand_pose_{index:02d}')
    for vertex,point in zip(key.data,points):vertex.co=point
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/WuduCanglan_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='RELATIVE')
print('EDITABLE_HAND_CHANNELS_SAVED',len(frames))
