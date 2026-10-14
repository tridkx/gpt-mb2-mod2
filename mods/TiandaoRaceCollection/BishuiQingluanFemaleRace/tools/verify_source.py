"""Reopen editable Blend and FBX and compare all visible source coordinates."""
import bpy,json,sys
import numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text());source=np.load(R/'build/fitted_model.npz');manifest=json.loads((R/'build/manifest.json').read_text());rows=[]
for kind in ['blend','fbx']:
 path=R/'source'/(cfg['id']+'_Rigged.'+kind)
 if kind=='blend':bpy.ops.wm.open_mainfile(filepath=str(path))
 else:bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
 arms=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(arms)==1 and len(arms[0].data.bones)==28
 errors=[]
 for rec in manifest:
  o=bpy.data.objects[rec['object']];p=np.array([o.matrix_world@v.co for v in o.data.vertices]);expected=source[rec['object']+'_p'];assert p.shape==expected.shape;error=float(abs(p-expected).max());assert error<3e-6;errors.append(error);assert o.data.uv_layers.active
  assert all(len([g for g in v.groups if g.weight>1e-7])<=4 for v in o.data.vertices)
 imgs=list({node.image for rec in manifest for mat in bpy.data.objects[rec['object']].data.materials for node in mat.node_tree.nodes if node.type=='TEX_IMAGE' and node.image});assert len(imgs)>=9
 for image in imgs:assert len(image.pixels)>0 and image.has_data
 if kind=='blend':assert all(im.packed_file for im in imgs)
 rows.append(dict(file=str(path.relative_to(R)),visible_meshes=len(manifest),bone_count=28,maximum_source_error_m=max(errors),images_loaded=len(imgs)))
(R/'reports/source_validation.json').write_text(json.dumps(dict(status='pass',files=rows),indent=2));print('EDITABLE_SOURCE_VERIFIED',rows)
