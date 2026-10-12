"""Compare source FBX coordinates and UV against editable source and final LOD0."""
import json,sys,subprocess
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if '--check' not in sys.argv:
    import bpy
    cfg=json.loads((R/'tools/model_config.json').read_text());manifest=json.loads((R/'build/manifest.json').read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'input/model.fbx'),use_anim=False)
    data={}
    for rec in manifest:
        o=bpy.data.objects[rec['source_object']];p=np.array([o.matrix_world@v.co for v in o.data.vertices])@np.array(cfg['source_rotation']).T*cfg['source_scale']
        data[rec['object']+'_p']=p
        o.data.calc_loop_triangles();loops=sorted({li for tri in o.data.loop_triangles if tri.area>1e-16 for li in tri.loops})
        vertices=sorted({o.data.loops[li].vertex_index for li in loops})
        data[rec['object']+'_surface']=p[vertices]
        data[rec['object']+'_pu']=np.array([list(p[o.data.loops[li].vertex_index])+list(o.data.uv_layers.active.data[li].uv) for li in loops])
    np.savez_compressed(R/'build/source_audit.npz',**data)
    subprocess.run(['C:/ProgramData/anaconda3/python.exe','-B','-X','utf8',__file__,'--check'],check=True)
    sys.exit(0)
sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
cfg=json.loads((R/'tools/model_config.json').read_text());manifest=json.loads((R/'build/manifest.json').read_text());arrays=np.load(R/'build/fitted_model.npz')
from scipy.spatial import cKDTree
source=np.load(R/'build/source_audit.npz')
meshes=[m for f in (R/'build/final_export_lod0/geo').glob('*.bin') for m in read_geo(f) if not m['name'].startswith('modern_girl_hidden')];rows=[]
for rec in manifest:
    p=source[rec['object']+'_p']
    source_error=float(abs(p-arrays[rec['object']+'_p']).max());assert source_error<1e-6
    groups=[m for m in meshes if m['name'].split('.b')[0]==rec['object']];q=np.concatenate([m['pos'] for m in groups]);u=np.concatenate([m['uv'] for m in groups]);u[:,1]=1-u[:,1]
    surface=source[rec['object']+'_surface'];error=float(cKDTree(q).query(surface)[0].max());assert error<2e-6,(rec['source_object'],error)
    sourcepu=source[rec['object']+'_pu']
    finalpu=np.concatenate([q,u],axis=1);uv_error=float(cKDTree(sourcepu).query(finalpu)[0].max());assert uv_error<2e-6
    rows.append(dict(part=rec['source_object'],source_error_m=source_error,final_lod0_error_m=error,position_uv_error=uv_error))
(R/'reports/preservation_validation.json').write_text(json.dumps(dict(status='pass',uniform_scale=cfg['source_scale'],rotation=cfg['source_rotation'],anatomy_warp=False,parts=rows),indent=2))
print('PROPORTIONS_AND_UV_PRESERVED',rows)
