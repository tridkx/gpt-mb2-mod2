"""Reopen editable deliverables and check packed textures/native bone order."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];cfg=json.loads((ROOT/'tools/model_config.json').read_text())
manifest=json.loads((ROOT/'build/rig_manifest.json').read_text());fit=json.loads((ROOT/'reports/rig_fit.json').read_text());arrays=np.load(ROOT/'build/rig_arrays.npz')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/ZhenwuYimo_Rigged.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
assert [b.name for b in rig.data.bones]==fit['bone_names'] and len(rig.data.bones)==28
matrix_errors=[float(np.max(abs(np.array(b.matrix_local)-arrays['world'][i]))) for i,b in enumerate(rig.data.bones)]
# Blender orthonormalises the rounded native matrices; this is a matrix-entry
# tolerance of 5e-5, while joint translations must match within one micron.
assert max(matrix_errors)<5e-5,matrix_errors
for i,b in enumerate(rig.data.bones):assert np.max(abs(np.array(b.matrix_local)[:3,3]-arrays['world'][i,:3,3]))<1e-6
for rec in manifest:
    o=bpy.data.objects[rec['object']];p=np.array([v.co for v in o.data.vertices]);assert np.max(abs(p-arrays[o.name+'_P']))<1e-6
    assert len(o.data.uv_layers)>0 and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)
    for v in o.data.vertices:assert 1<=len(v.groups)<=4 and abs(sum(g.weight for g in v.groups)-1)<1e-5
    for material in o.data.materials:
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                assert node.image.packed_file is not None
                node.image.pixels[0];assert node.image.has_data and node.image.size[0]>0
report={'status':'pass','meshes':len(manifest),'bones':28,'native_rest_matrices_match':True,'max_native_matrix_entry_error':max(matrix_errors),'all_used_textures_packed':True,'source_matches_export_arrays':True}
rigged_uv={r['source_object']:np.array([u.uv[:] for u in bpy.data.objects[r['object']].data.uv_layers.active.data]) for r in manifest}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'input/model.fbx'),use_anim=False)
uv_records=[]
for original,actual in rigged_uv.items():
    expected=np.array([u.uv[:] for u in bpy.data.objects[original].data.uv_layers.active.data])
    flipped=original in cfg.get('uv_flip_v_objects',[])
    if flipped:expected[:,1]=1-expected[:,1]
    error=float(abs(actual-expected).max());assert error<1e-6,(original,'UV mapping differs',error)
    uv_records.append({'source_mesh':original,'flip_v':flipped,'max_error':error})
report['uv_verified']=uv_records
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'source/ZhenwuYimo_Rigged.fbx'),use_anim=False)
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(rigs)==1 and len(rigs[0].data.bones)==28
assert len([o for o in bpy.data.objects if o.type=='MESH'])==len(manifest)
report['fbx_reimport_verified']=True
original=Path(cfg['original_directory'])
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
preserved=[]
for file in [ROOT/'input/model.fbx',*sorted((ROOT/'tex').glob('*.png'))]:
    origin=original/('model.fbx' if file.suffix=='.fbx' else 'tex/'+file.name)
    assert sha(file)==sha(origin)
    preserved.append({'original':str(origin),'copy':str(file.relative_to(ROOT)),'sha256':sha(file)})
(ROOT/'reports/input_preservation.json').write_text(json.dumps({'status':'pass','files':preserved},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'reports/source_validation.json').write_text(json.dumps(report,indent=2));print('EDITABLE_SOURCE_VERIFIED',report)
