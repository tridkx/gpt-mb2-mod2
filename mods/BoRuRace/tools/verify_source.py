"""Reopen both editable source files and confirm packed texture and rig data."""
import bpy,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'build/manifest.json').read_text())
blend=ROOT/'source/BoRuRace_Rigged.blend';fbx=ROOT/'source/BoRuRace_Rigged.fbx'
bpy.ops.wm.open_mainfile(filepath=str(blend))
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'];meshes=[o for o in bpy.data.objects if o.type=='MESH'];images=[i for i in bpy.data.images if i.type=='IMAGE' and i.source=='FILE']
assert len(arm)==1 and len(arm[0].data.bones)==28 and len(meshes)==len(manifest)
assert images and all(i.packed_file for i in images)
assert all(any(m.type=='ARMATURE' and m.object==arm[0] for m in o.modifiers) for o in meshes)
arrays=np.load(ROOT/'build/fitted_model.npz')
for o in meshes:
    p=np.array([v.co for v in o.data.vertices]);assert np.max(np.abs(p-arrays[o.name+'_p']))<1e-6
    w=np.zeros((len(p),28))
    for v in o.data.vertices:
        for g in v.groups:w[v.index,int(o.vertex_groups[g.group].name.rsplit('_',1)[1])]=g.weight
    assert np.max(np.abs(w-arrays[o.name+'_w']))<1e-6
assert fbx.is_file() and fbx.stat().st_size>1000000
image_count=len(images)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(fbx),use_anim=False)
arms=[o for o in bpy.data.objects if o.type=='ARMATURE'];fbxmeshes=[o for o in bpy.data.objects if o.type=='MESH']
assert len(arms)==1 and len(arms[0].data.bones)==28 and len(fbxmeshes)==len(manifest)
(ROOT/'reports/source_validation.json').write_text(json.dumps({'status':'pass','blend_reopened':True,'fbx_reimported':True,'source_matches_original_geometry':True,'anatomy_warp_applied':False,'bones':28,'meshes':len(manifest),'packed_images':image_count,'facial_animation':False},indent=2))
print('SOURCE_VALIDATED')
