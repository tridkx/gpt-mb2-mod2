"""Reopen editable sources and check geometry and embedded textures."""
import bpy,json,sys
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from finger_rig import pose_world
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
    assert len(ob.vertex_groups)==58 and len(ob.data.uv_layers)>0
    for v in ob.data.vertices:assert 1<=len(v.groups)<=4 and abs(sum(g.weight for g in v.groups)-1)<1e-5
assert all(im.packed_file is not None for im in bpy.data.images if im.source=='FILE')
blend_images=sum(1 for im in bpy.data.images if im.source=='FILE')
blend_hand_error=verify_hand_keys()
arm=bpy.data.objects['wdr_skeleton'];assert len(arm.data.bones)==58
spec=json.loads((R/'build/skeleton_spec.json').read_text())
# Blender joint directions must agree with the delivered skeleton, not just heads.
world=[]
for i,b in enumerate(spec):
    local=np.array(b['rest']).reshape(4,4).T;local[3]=[0,0,0,1]
    world.append(local if b['parent']<0 else world[b['parent']]@local)
    assert np.max(abs(np.array(arm.data.bones[b['name']+'_'+str(i)].matrix_local)-world[-1]))<5e-5
assert arm.animation_data is not None and arm.animation_data.action is not None
hand=bpy.data.objects['wdr_part_04'];rest=np.array([v.co[:] for v in hand.data.vertices])
assert all(key.value==0 for key in hand.data.shape_keys.key_blocks[1:])
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
evaluated=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());opened=np.array([v.co[:] for v in evaluated.data.vertices])
assert np.max(abs(opened-rest))<1e-5
bpy.context.scene.frame_set(30);bpy.context.view_layer.update()
evaluated=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());closed=np.array([v.co[:] for v in evaluated.data.vertices])
finger_motion=float(np.linalg.norm(closed-rest,axis=1).max());assert .025<finger_motion<.15
parents=np.array([b['parent'] for b in spec]);rest_world=np.array(world)
locals=np.array([np.array(b['rest']).reshape(4,4).T for b in spec]);locals[:,3]=[0,0,0,1]
posed_world=pose_world(dict(restWorld=rest_world,restLocal=locals,parent=parents),1,1)
skin=posed_world@np.linalg.inv(rest_world);predicted=np.zeros_like(rest)
for vertex in hand.data.vertices:
    for group in vertex.groups:
        bone=int(hand.vertex_groups[group.group].name.rsplit('_',1)[1]);predicted[vertex.index]+=group.weight*(skin[bone]@np.r_[vertex.co[:],1])[:3]
finger_error=float(np.max(abs(predicted-closed)));assert finger_error<5e-5
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'source/WuduCanglan_Rigged.fbx'),use_anim=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)==13
armatures=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(armatures)==1 and len(armatures[0].data.bones)==58
for ob in meshes:
    p=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);err=float(abs(p-expected[ob.name+'_p']).max());max_error=max(max_error,err);assert err<1e-5
fbx_hand_error=verify_hand_keys()
(R/'reports/editable_source_validation.json').write_text(json.dumps(dict(status='pass',blend_reopened=True,fbx_reopened=True,packed_images=blend_images,max_vertex_error_m=max_error,hand_morph_channels=26,bones=58,finger_joints=30,blend_finger_animation_max_motion_m=finger_motion,blend_finger_animation_vs_offline_max_error_m=finger_error,blend_hand_morph_error_m=blend_hand_error,fbx_hand_morph_error_m=fbx_hand_error),indent=2))
print('EDITABLE_SOURCES_VERIFIED',max_error)
