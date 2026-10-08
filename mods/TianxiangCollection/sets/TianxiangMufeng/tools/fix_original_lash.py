"""Prepare an unrigged original FBX UV correction; verify geometry round-trip."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'input/model.fbx'),use_anim=False)
before={}
for o in bpy.context.scene.objects:
    if o.type=='MESH':before[o.name]=np.array([o.matrix_world@v.co for v in o.data.vertices])
assert len(before)==14 and not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
o=bpy.data.objects['mesh_04_414907']
for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
expected={}
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    expected[o.name]={(tuple(np.round(before[o.name][l.vertex_index],3)),tuple(np.round(o.data.uv_layers.active.data[l.index].uv,5))) for l in o.data.loops}
    for mat in o.data.materials:
        for n in mat.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image:
                n.image.filepath=str(Path('D:/dsh-tiandao/天香少女校服8套/02沐风为裳/tex')/Path(n.image.filepath).name);n.image.reload()
out=ROOT/'source/OriginalModel_LashFixed.fbx'
bpy.ops.export_scene.fbx(filepath=str(out),object_types={'MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(out),use_anim=False)
errors=[]
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    p=np.array([o.matrix_world@v.co for v in o.data.vertices]);assert p.shape==before[o.name].shape
    errors.append(float(np.max(abs(p-before[o.name]))));assert errors[-1]<.001
    keys={(tuple(np.round(p[l.vertex_index],3)),tuple(np.round(o.data.uv_layers.active.data[l.index].uv,5))) for l in o.data.loops}
    assert keys==expected[o.name],o.name
report={'status':'pass','meshes':14,'rig_added':False,'changed_uv_object':'mesh_04_414907','max_coordinate_error_source_units':max(errors),'original_input_sha256':hashlib.sha256((ROOT/'input/model.fbx').read_bytes()).hexdigest(),'fixed_fbx_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(ROOT/'reports/original_lash_fix.json').write_text(json.dumps(report,indent=2));print('ORIGINAL_LASH_FIX_VERIFIED',report)
