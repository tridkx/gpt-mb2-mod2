import bpy,sys,json
import numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sleeve_skinning import apply
R=Path(__file__).resolve().parents[1];path=R/'build/fitted_model.npz';raw=np.load(path);data={k:raw[k] for k in raw.files};p=data['bql_part_13_p'];old=data['bql_part_13_w'];others=np.concatenate([v for k,v in data.items() if k.endswith('_p') and k!='bql_part_13_p']);w,contact=apply(p,old,others);data['bql_part_13_w']=w.astype('f4');np.savez_compressed(path,**data)
bpy.ops.wm.open_mainfile(filepath=str(R/'source/BishuiQingluanFemaleRace_Rigged.blend'));o=bpy.data.objects['bql_part_13'];assert len(o.data.vertices)==len(p)
for group in o.vertex_groups:group.remove(list(range(len(p))))
for i in range(28):
    group=next(g for g in o.vertex_groups if g.name.endswith('_'+str(i)))
    for vi in np.flatnonzero(w[:,i]>1e-7):group.add([int(vi)],float(w[vi,i]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/BishuiQingluanFemaleRace_Rigged.blend'));bpy.ops.export_scene.fbx(filepath=str(R/'source/BishuiQingluanFemaleRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
(R/'reports/sleeve_skinning.json').write_text(json.dumps(dict(method='Shared height reference, rigid forearm on hanging sleeve, common smooth proximal transition',changed_vertices=int((abs(w-old).max(1)>1e-6).sum()),skin_contact_vertices_preserved=int(contact.sum()),geometry_changed=False,cloth_enabled=False),indent=2))
