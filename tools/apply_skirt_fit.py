"""Apply calibrated skirt only to preserved editable release; keep other meshes."""
import bpy,sys,json,shutil
import numpy as np
from pathlib import Path
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[sys.argv.index('--')+1];BASE=ROOT/'build/repair_baseline_v1.0.0'
bpy.ops.wm.open_mainfile(filepath=str(BASE/f'source/{ROOT.name}_Rigged.blend'))
f=np.load(ROOT/'build/skirt_clearance_fit.npz');name=str(f['object']);o=bpy.data.objects[name];assert len(o.data.vertices)==len(f['P'])
for v,p in zip(o.data.vertices,f['P']):v.co=p
for group in o.vertex_groups:group.remove(list(range(len(o.data.vertices))))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');bones=list(rig.data.bones)
for i,b in enumerate(bones):
    for vi in np.where(f['W'][:,i]>1e-6)[0]:o.vertex_groups[b.name].add([int(vi)],float(f['W'][vi,i]),'REPLACE')
alpha=f['A'] if 'A' in f.files else np.zeros(len(f['P']))
colors=np.ones((len(f['P']),4));colors[:,3]=alpha;o.data.color_attributes['ClothDistance'].data.foreach_set('color',colors.ravel())
# User-visible leg clearance must not depend on an unverified game cloth solve.
fitfile=ROOT/'source/SkirtClearanceFit.npz';np.savez_compressed(fitfile,P=f['P'],W=f['W'],A=alpha,object=name)
cfgpath=ROOT/'tools/model_config.json';cfg=json.loads(cfgpath.read_text());cfg['skirt_clearance_fit']='source/SkirtClearanceFit.npz';cfg['skirt_physics_enabled']=bool(alpha.max()>.001);cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
a=dict(np.load(BASE/'rig_arrays.npz'));a[name+'_P']=f['P'];a[name+'_W']=f['W'];a[name+'_A']=alpha;np.savez_compressed(ROOT/'build/rig_arrays.npz',**a)
manifest=json.loads((BASE/'rig_manifest.json').read_text())
for r in manifest:
    if r['object']==name:r.update(cloth=bool(alpha.max()>.001),max_distance=float(alpha.max()),bounds=[f['P'].min(0).tolist(),f['P'].max(0).tolist()])
(ROOT/'build/rig_manifest.json').write_text(json.dumps(manifest,indent=2))
fit=json.loads((BASE/'reports/rig_fit.json').read_text());fit['parts']=manifest;(ROOT/'reports/rig_fit.json').write_text(json.dumps(fit,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'source/{ROOT.name}_Rigged.blend'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=str(ROOT/f'source/{ROOT.name}_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
print('SKIRT_ONLY_FIT_APPLIED',ROOT.name,name)
