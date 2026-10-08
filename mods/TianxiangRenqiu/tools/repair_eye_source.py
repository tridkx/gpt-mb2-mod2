"""v1.0.0 -> v1.0.1: isolated lash UV/material edit; no rebinding."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
# Always start at the preserved release, so this repair is idempotent.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'build/eye_baseline_v1.0.0/TianxiangRenqiu_Rigged.blend'))
o=bpy.data.objects['rq1_head_03']
for uv in o.data.uv_layers.active.data:uv.uv.y=1-uv.uv.y
for o in bpy.context.scene.objects:
    if o.type!='MESH' or o.name not in ['rq1_head_03','rq1_head_09']:continue
    mat=o.data.materials[0];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
    test=mat.node_tree.nodes.new('ShaderNodeMath');test.operation='GREATER_THAN';test.inputs[1].default_value=cfg['material_overrides']['lash']['alphaTest']
    mat.node_tree.links.new(tex.outputs['Alpha'],test.inputs[0]);mat.node_tree.links.new(test.outputs[0],bs.inputs['Alpha'])
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/TianxiangRenqiu_Rigged.blend'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/TianxiangRenqiu_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
print('EYE_SOURCE_REPAIRED')
