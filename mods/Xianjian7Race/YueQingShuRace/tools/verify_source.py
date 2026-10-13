"""Reopen both editable source files and confirm packed texture and rig data."""
import bpy,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
blend=ROOT/'source/YueQingShuRace_Rigged.blend';fbx=ROOT/'source/YueQingShuRace_Rigged.fbx'
bpy.ops.wm.open_mainfile(filepath=str(blend))
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'];meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('yqs_cloth_proxy')];images=[i for i in bpy.data.images if i.type=='IMAGE' and i.source=='FILE']
assert len(arm)==1 and len(arm[0].data.bones)==28 and len(meshes)==10
assert images and all(i.packed_file for i in images)
assert all(i.filepath.replace('\\','/').startswith('//../tex/') and (ROOT/'tex'/Path(i.filepath).name).is_file() for i in images)
assert all(any(m.type=='ARMATURE' and m.object==arm[0] for m in o.modifiers) for o in meshes)
arrays=np.load(ROOT/'build/fitted_model.npz')
for o in meshes:
    p=np.array([v.co for v in o.data.vertices]);assert np.max(np.abs(p-arrays[o.name+'_p']))<1e-6
    w=np.zeros((len(p),28))
    for v in o.data.vertices:
        for g in v.groups:w[v.index,int(o.vertex_groups[g.group].name.rsplit('_',1)[1])]=g.weight
    assert np.max(np.abs(w-arrays[o.name+'_w']))<1e-6
alphas=np.load(ROOT/'build/cloth_alphas.npz')
for o in meshes:
    colors=o.data.color_attributes.get('ClothDistance');assert colors and colors.domain=='POINT'
    actual=np.array([v.color[3] for v in colors.data]);assert np.max(abs(actual-alphas[o.name]))<1e-6
assert fbx.is_file() and fbx.stat().st_size>1000000
image_count=len(images)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(fbx),use_anim=False)
arms=[o for o in bpy.data.objects if o.type=='ARMATURE'];fbxmeshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('yqs_cloth_proxy')]
assert len(arms)==1 and len(arms[0].data.bones)==28 and len(fbxmeshes)==10
# Independent comparison against the preserved original, after re-opening it.
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/cfg['source_blend']))
original=next(o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('yqs_cloth_proxy'))
rotation=np.diag([-1.,-1.,1.]);source=np.array([original.matrix_world@v.co for v in original.data.vertices])@rotation
manifest=json.loads((ROOT/'build/manifest.json').read_text());errors=[]
for rec in manifest:
 mi=next(i for i,slot in enumerate(original.material_slots) if slot.material.name==rec['material'])
 ids=set(v for face in original.data.polygons if face.material_index==mi for v in face.vertices)
 points=source[sorted(ids)];final=arrays[rec['object']+'_p']
 reference=np.unique(points.astype('f4'),axis=0);exported=np.unique(final,axis=0)
 assert reference.shape==exported.shape,(rec['material'],reference.shape,exported.shape)
 error=float(np.max(np.abs(reference-exported)));assert error<2e-6,(rec['material'],error)
 errors.append(dict(material=rec['material'],max_geometry_error_m=error))
report={'status':'pass','blend_reopened':True,'fbx_reimported':True,'source_matches_final_fit':True,'bones':28,'meshes':10,'packed_images':image_count,'facial_animation':False,'game_cloth_paint_verified':True,'cloth_engine_verified':False,'source_proportions_preserved':True,'source_height_m':float(np.ptp(source[:,2])),'source_geometry_checks':errors,'source_geometry_max_error_m':max(e['max_geometry_error_m'] for e in errors)}
(ROOT/'reports/source_validation.json').write_text(json.dumps(report,indent=2))
print('SOURCE_VALIDATED',report['source_geometry_max_error_m'])
