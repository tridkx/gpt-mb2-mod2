"""Reopen experimental Blend and FBX; verify the released source is preserved."""
from pathlib import Path
import json, hashlib
import bpy
import numpy as np

R=Path(__file__).resolve().parents[1]
def geometry():
    result={}
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name!='yqs_cloth_proxy':
            p=np.empty(len(o.data.vertices)*3,'f4');o.data.vertices.foreach_get('co',p)
            result[o.name]=p
    return result

original=R/'source/YueQingShuRace_Rigged.blend'
blend=R/'source/YueQingShuRace_SkirtProxy_Experimental.blend'
fbx=R/'source/YueQingShuRace_SkirtProxy_Experimental.fbx'
bpy.ops.wm.open_mainfile(filepath=str(original)); before=geometry()
bpy.ops.wm.open_mainfile(filepath=str(blend)); after=geometry()
assert before.keys()==after.keys()
assert all(np.array_equal(before[n],after[n]) for n in before)
obj=bpy.data.objects['yqs_cloth_proxy']
source=json.loads((R/'build/proxy_source.json').read_text())
assert len(obj.data.vertices)==len(source['positions']) and obj.hide_render
p=np.empty(len(obj.data.vertices)*3,'f4');obj.data.vertices.foreach_get('co',p)
assert np.isfinite(p).all() and np.max(abs(p.reshape(-1,3)-source['positions']))<1e-7
assert len(obj.vertex_groups)==28
missing=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
assert not missing, missing
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(fbx))
obj=next(o for o in bpy.data.objects if o.name.startswith('yqs_cloth_proxy'))
assert len(obj.data.vertices)==len(source['positions'])
assert any(o.type=='ARMATURE' for o in bpy.data.objects)
report=dict(status='pass',experimental=True,proxy_vertices=len(source['positions']),
    visible_blend_geometry_identical=True,blend_textures_packed=True,fbx_reopened=True,
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [original,blend,fbx]})
(R/'reports/experiments/simplified_skirt_2026-10-14/source_validation.json').write_text(json.dumps(report,indent=2))
print('EXPERIMENTAL_SOURCE_VERIFIED',len(source['positions']))
