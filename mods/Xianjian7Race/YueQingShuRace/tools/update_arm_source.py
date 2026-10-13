"""Apply corrected rest matrices to editable sources without changing any mesh."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from workspace_paths import workspace_root
sys.path.insert(0,str(workspace_root(R)/'tools/asset_helpers/previewer'));from baker.skeleton import parse_skeljson
rig=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((R/'build/skeleton_spec.json').read_text()))]});bpy.ops.wm.open_mainfile(filepath=str(R/'source/YueQingShuRace_Rigged.blend'));arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for i,name in enumerate(rig['names']):b=arm.data.edit_bones[name+'_'+str(i)];b.matrix=Matrix(rig['restWorld'][i].tolist());b.length=.03
bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/YueQingShuRace_Rigged.blend'));bpy.ops.export_scene.fbx(filepath=str(R/'source/YueQingShuRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
