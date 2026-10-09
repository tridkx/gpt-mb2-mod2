import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
original=next(o for o in bpy.context.scene.objects if o.type=='MESH');expected=np.array([original.matrix_world@v.co for v in original.data.vertices])*np.array([-1,-1,1])*.015
bpy.ops.wm.open_mainfile(filepath=str(R/'source/Feifeng_Source_150.blend'));source=next(o for o in bpy.context.scene.objects if o.type=='MESH');actual=np.array([source.matrix_world@v.co for v in source.data.vertices]);assert actual.shape==expected.shape
error=float(abs(actual-expected).max());assert error<1e-6,error
packed=[]
for image in bpy.data.images:
 if image.source=='FILE':assert image.packed_file is not None and image.size[0]>0;packed.append(image.name)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'source/Feifeng_Source_150.fbx'),use_anim=False)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];points=np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices]) for o in objects]);height=float(np.ptp(points[:,2]));assert abs(height-np.ptp(expected[:,2]))<1e-5
bpy.ops.wm.open_mainfile(filepath=str(R/'source/Feifeng_Test_Rigged.blend'));assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==20
for image in bpy.data.images:
 if image.source=='FILE':assert image.packed_file is not None and image.size[0]>0
report=dict(status='pass',literal_source_scale=1.5,max_coordinate_error_m=error,fbx_height_m=height,packed_images=packed,rigged_meshes=20)
(R/'reports/source_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
