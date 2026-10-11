"""Store the same 26 hand channels in the editable Blend and FBX."""
import bpy,numpy as np,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
hand=bpy.data.objects['wdr_part_04'];hand.shape_key_clear();hand.shape_key_add(name='Basis')
frames=np.load(R/'build/hand_source_shapes.npz')['frames']
for index,points in enumerate(frames):
    key=hand.shape_key_add(name=f'hand_pose_{index:02d}')
    key.value=0
    for vertex,point in zip(key.data,points):vertex.co=point
arm=bpy.data.objects['wdr_skeleton']
for bone in arm.pose.bones:
    if int(bone.name.rsplit('_',1)[1])<28:continue
    index=int(bone.name.rsplit('_',1)[1])-28
    bone.rotation_mode='XYZ'
    for frame,value in [(1,0),(30,1),(60,0)]:
        bone.rotation_euler.x=math.radians([48,62,42][index%3])*value
        bone.keyframe_insert(data_path='rotation_euler',frame=frame,group=bone.name)
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=60;bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/WuduCanglan_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='RELATIVE')
print('EDITABLE_HAND_CHANNELS_SAVED',len(frames))
