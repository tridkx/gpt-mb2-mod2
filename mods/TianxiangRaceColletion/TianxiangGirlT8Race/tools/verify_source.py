"""Reopen editable files and compare with original input coordinates."""
import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cfg=json.loads((R/'tools/model_config.json').read_text())
manifest=json.loads((R/'build/manifest.json').read_text());arrays=np.load(R/'build/fitted_model.npz')
bpy.ops.wm.open_mainfile(filepath=str(R/'source/TianxiangGirlT8Race_Rigged.blend'))
arms=[o for o in bpy.data.objects if o.type=='ARMATURE'];meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert len(arms)==1 and len(arms[0].data.bones)==28 and len(meshes)==len(manifest)
images=[im for im in bpy.data.images if im.source=='FILE'];assert images and all(im.packed_file for im in images)
skirt=bpy.data.objects[cfg['skirt_object']];layer=skirt.data.color_attributes['ClothDistance']
alphas=np.array([c.color[3] for c in layer.data]);paint=json.loads((R/'reports/cloth_paint.json').read_text());assert int((alphas==0).sum())==paint['fixed_vertices'] and abs(alphas.max()-paint['max_travel_m'])<1e-6
for o in meshes:
    assert np.max(abs(np.array([v.co for v in o.data.vertices])-arrays[o.name+'_p']))<1e-6
    assert any(m.type=='ARMATURE' and m.object==arms[0] for m in o.modifiers)
    weights=np.zeros((len(o.data.vertices),28))
    for v in o.data.vertices:
        for g in v.groups:weights[v.index,int(o.vertex_groups[g.group].name.rsplit('_',1)[1])]=g.weight
    assert np.max(abs(weights-arrays[o.name+'_w']))<1e-6
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'source/TianxiangGirlT8Race_Rigged.fbx'),use_anim=False)
arms=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(arms)==1 and len(arms[0].data.bones)==28
assert len([o for o in bpy.data.objects if o.type=='MESH'])==len(manifest)
skirt=bpy.data.objects[cfg['skirt_object']];layer=skirt.data.color_attributes.get('ClothDistance');assert layer is not None
fbx_alpha=np.array([c.color[3] for c in layer.data]);assert (fbx_alpha==0).any() and abs(fbx_alpha.max()-paint['max_travel_m'])<.006
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
errors=[]
for rec in manifest:
    ob=bpy.data.objects[rec['source_object']];p=np.array([ob.matrix_world@v.co for v in ob.data.vertices])*.01
    error=float(np.max(abs(p-arrays[rec['object']+'_p'])))
    if rec['object']==cfg['skirt_object']:
        assert np.max(abs(p[:,2]-arrays[rec['object']+'_p'][:,2]))<1e-6
        fit=json.loads((R/'reports/preview_skirt_fit.json').read_text())['parts'][0]
        assert error<=fit['maximum_offset_m']+1e-6
    else:assert error<1e-6
    errors.append({'part':rec['object'],'max_error_m':error})
report={'status':'pass','blend_reopened':True,'fbx_reimported':True,'packed_images':len(images),'meshes':len(manifest),'bones':28,'source_proportions_preserved':True,'source_geometry_max_error_m':max(x['max_error_m'] for x in errors),'parts':errors}
(R/'reports/source_validation.json').write_text(json.dumps(report,indent=2));print(report)
