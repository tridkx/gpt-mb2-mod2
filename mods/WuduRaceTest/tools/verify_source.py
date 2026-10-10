"""Reopen editable sources and check geometry and embedded textures."""
import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
expected=np.load(R/'build/source_positions.npz')
bpy.ops.wm.open_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
manifest=json.loads((R/'build/rig_manifest.json').read_text());max_error=0
for row in manifest:
    ob=bpy.data.objects[row['object']];p=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);err=float(abs(p-expected[ob.name+'_p']).max());max_error=max(max_error,err);assert err<1e-6
    assert len(ob.vertex_groups)==28 and len(ob.data.uv_layers)>0
    for v in ob.data.vertices:assert 1<=len(v.groups)<=4 and abs(sum(g.weight for g in v.groups)-1)<1e-5
assert all(im.packed_file is not None for im in bpy.data.images if im.source=='FILE')
blend_images=sum(1 for im in bpy.data.images if im.source=='FILE')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'source/WuduCanglan_Rigged.fbx'),use_anim=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)==13
armatures=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(armatures)==1 and len(armatures[0].data.bones)==28
for ob in meshes:
    p=np.array([ob.matrix_world@v.co for v in ob.data.vertices]);err=float(abs(p-expected[ob.name+'_p']).max());max_error=max(max_error,err);assert err<1e-5
(R/'reports/editable_source_validation.json').write_text(json.dumps(dict(status='pass',blend_reopened=True,fbx_reopened=True,packed_images=blend_images,max_vertex_error_m=max_error),indent=2))
print('EDITABLE_SOURCES_VERIFIED',max_error)
