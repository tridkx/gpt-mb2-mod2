"""Reopen saved Blend and FBX; verify geometry preservation and packed textures."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    state={}
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or o.name.endswith('_cloth_preview'):continue
        state[o.name]={'pos':np.array([v.co for v in o.data.vertices]),'faces':[list(p.vertices) for p in o.data.polygons],'uv':np.array([v.uv for v in o.data.uv_layers.active.data]),'weights':[[[o.vertex_groups[g.group].name,round(g.weight,7)] for g in v.groups] for v in o.data.vertices],'alpha':np.array([c.color[3] for c in o.data.color_attributes['ClothDistance'].data])}
    return state
before=snapshot(ROOT/'build/sleeve_baseline/TianxiangT5_Rigged.blend')
after=snapshot(ROOT/'source/TianxiangT5_Rigged.blend')
assert before.keys()==after.keys()
for name in before:
    for field in ['pos','uv']:assert np.array_equal(before[name][field],after[name][field]),(name,field)
    for field in ['faces','weights']:assert before[name][field]==after[name][field],(name,field)
    if name!='tx5_body_00':assert np.array_equal(before[name]['alpha'],after[name]['alpha']),name
images=[]
for img in bpy.data.images:
    if img.source!='FILE':continue
    assert img.packed_file is not None,img.name
    pixels=np.array(img.pixels[:])
    assert len(pixels)==img.size[0]*img.size[1]*4 and np.isfinite(pixels).all() and len(pixels)>0,img.name
    images.append({'name':img.name,'size':list(img.size),'packed':True})
# The FBX is a supplemental editable export; the Blend preserves precise masks
# and runtime distance multiplier. Check it can be imported and contains skin.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'source/TianxiangT5_Rigged.fbx'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(objects)==len(after)
for o in objects:
    assert len(o.data.vertices)>0 and all(len(v.groups)>0 for v in o.data.vertices),o.name
    assert np.isfinite(np.array([v.co for v in o.data.vertices])).all(),o.name
report={'status':'pass','blend_reopened':True,'fbx_reimported':True,'source_geometry_uv_and_weights_preserved':True,'only_sleeve_alpha_changed':True,'packed_images':images,'fbx_mesh_count':len(objects),'blend_sha256':hashlib.sha256((ROOT/'source/TianxiangT5_Rigged.blend').read_bytes()).hexdigest(),'fbx_sha256':hashlib.sha256((ROOT/'source/TianxiangT5_Rigged.fbx').read_bytes()).hexdigest()}
(ROOT/'reports/sleeve_source_validation.json').write_text(json.dumps(report,indent=2))
print('SLEEVE_SOURCE_VALIDATED',len(images),'packed images',len(objects),'FBX meshes')
