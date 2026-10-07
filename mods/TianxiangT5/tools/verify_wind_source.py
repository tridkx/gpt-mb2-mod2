"""Reopen exact historical source and import both FBX exports."""
from pathlib import Path
import bpy,json,numpy as np
ROOT=Path(__file__).resolve().parents[1];checks=[]
for stem,count in [('TianxiangT5_Rigged',14),('TianxiangT5_ClothSimulation',1)]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source'/(stem+'.blend')))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith('_cloth_preview')]
    assert len(meshes)==count
    images=[i for i in bpy.data.images if i.source=='FILE']
    assert images and all(i.packed_file is not None for i in images)
    for o in meshes:assert np.isfinite(np.array([v.co for v in o.data.vertices])).all()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/'source'/(stem+'.fbx')))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==count
    assert all(all(len(v.groups)>0 for v in o.data.vertices) for o in objects)
    checks.append({'source':stem,'blend_reopened':True,'fbx_reimported':True,'mesh_count':count,'packed_images':len(images)})
(ROOT/'reports/wind_control_source_validation.json').write_text(json.dumps({'status':'pass','checks':checks},indent=2))
