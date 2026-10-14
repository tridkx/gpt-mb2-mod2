"""Reopen editable Blender and FBX; compare original source shape and UVs."""
import bpy,sys,json
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parents[1];C=json.loads((R/'tools/model_config.json').read_text());raw=np.load(R/'build/raw_model.npz');p=raw['p']@np.array(C['source_rotation']).T*C['unit_scale'];p[:,2]-=raw['p'][:,1].min()*C['unit_scale'];rows=json.loads((R/'build/manifest.json').read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(R/'source/EmilieRace_Rigged.blend'));assert len([o for o in bpy.data.objects if o.type=='ARMATURE'])==1;assert len(bpy.data.objects['emilie_skeleton'].data.bones)==28;errors=[]
for rec in rows:
 o=bpy.data.objects[rec['object']];ix=np.array(rec['source_vertex_indices']);actual=np.array([v.co for v in o.data.vertices]);e=float(abs(actual-p[ix]).max());assert e<1e-6
 loop_ix=np.array([loop.vertex_index for loop in o.data.loops]);expected=raw['uv'][ix[loop_ix]].copy();expected[:,1]=1-expected[:,1];actual_uv=np.empty(len(loop_ix)*2);o.data.uv_layers.active.data.foreach_get('uv',actual_uv);assert abs(actual_uv.reshape(-1,2)-expected).max()<1e-6
 assert all(abs(sum(g.weight for g in v.groups)-1)<.0001 for v in o.data.vertices)
 for mat in o.data.materials:
  assert all(n.image.packed_file for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
 errors.append({'mesh':o.name,'vertices':len(actual),'max_source_position_error_m':e,'uv_preserved':True})
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'source/EmilieRace_Rigged.fbx'),use_anim=False);objects=[o for o in bpy.data.objects if o.type=='MESH'];assert len(objects)==len(rows);actual=np.concatenate([np.array([o.matrix_world@v.co for v in o.data.vertices]) for o in objects]);tree=KDTree(len(p))
for i,co in enumerate(p):tree.insert(co,i)
tree.balance();dist=np.array([tree.find(co)[2] for co in actual]);assert dist.max()<2e-6;assert len([o for o in bpy.data.objects if o.type=='ARMATURE'])==1
(R/'reports/source_validation.json').write_text(json.dumps({'status':'pass','blend_reopened':True,'fbx_reopened':True,'source_proportions_preserved':True,'uniform_scale':C['unit_scale'],'fbx_max_source_position_error_m':float(dist.max()),'meshes':errors},indent=2));print('EDITABLE_SOURCE_VERIFIED',len(objects))
