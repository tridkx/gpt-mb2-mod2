"""Check requested rear patches from final TPAC geometry in every LOD."""
import bpy, json, sys, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'D:\gpt-mb2-mod\tools')
from georead import read_geo
checks=[]
source_only='--source-only' in sys.argv
if source_only:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.blend'))
    source_meshes=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        o.data.calc_loop_triangles()
        source_meshes.append({'name':o.name,'pos':np.array([v.co[:] for v in o.data.vertices]),'idx':np.array([t.vertices[:] for t in o.data.loop_triangles])})
# The top V is the garment's collar opening. The back core below it and the
# round opening below the belt are the requested missing clothing surfaces.
regions=[('back_below_collar','hbr_body_29',(-.045,.045),(1.14,1.38)),('waist','hbr_body_18',(-.035,.035),(.995,1.035))]
for lod in ([0] if source_only else range(4)):
    folder=ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')
    meshes=source_meshes if source_only else [m for p in (folder/'geo').glob('*.bin') for m in read_geo(p)]
    for label,name,xrange,zrange in regions:
        rows=[m for m in meshes if m['name'].split('.lod')[0].split('.b')[0]==name]
        verts=[];faces=[]
        for m in rows:
            offset=len(verts);verts.extend(m['pos'].tolist());faces.extend((m['idx'].reshape(-1,3)+offset).tolist())
        tree=BVHTree.FromPolygons(verts,faces,all_triangles=True)
        hits=[];failed=[]
        for x in np.linspace(*xrange,9):
            for z in np.linspace(*zrange,15):
                p,n,index,d=tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4)
                hits.append(p is not None and p.y<.005)
                if not hits[-1]:failed.append([float(x),float(z),list(p) if p else None])
        if failed:print('FAILED_RAYS',lod,label,failed)
        assert all(hits),(lod,label,sum(hits),len(hits))
        checks.append({'lod':lod,'region':label,'rear_surface_rays':len(hits),'rear_surface_hits':sum(hits)})
# Compare the accepted source outside the repaired garment parts. Include
# vertex positions, original topology and weights, not only counts.
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {o.name:{'positions':np.array([v.co[:] for v in o.data.vertices]),'faces':[tuple(f.vertices) for f in o.data.polygons],
          'weights':[tuple((o.vertex_groups[g.group].name,round(g.weight,6)) for g in v.groups) for v in o.data.vertices]}
          for o in bpy.context.scene.objects if o.type=='MESH'}
baseline=ROOT/'build/baseline_v1.0.0/HanfuBlueRed_Rigged.blend'
unchanged=[]
if baseline.exists():
    old=snapshot(baseline);new=snapshot(ROOT/'source/HanfuBlueRed_Rigged.blend')
    for name,a in old.items():
        if name in ['hbr_body_18','hbr_body_29']:continue
        b=new[name]
        assert np.array_equal(a['positions'],b['positions']),name
        assert a['faces']==b['faces'] and a['weights']==b['weights'],name
        unchanged.append(name)
report={'version':'v1.0.1','status':'pass','final_package_sha256':hashlib.sha256((ROOT/'module/HanfuBlueRed/AssetPackages/hbr.tpac').read_bytes()).hexdigest(),
        'coverage':checks,'unchanged_source_meshes':unchanged,'repair':json.loads((ROOT/'reports/rig_fit.json').read_text())['hair_surface_repairs'],
        'texture_note':'Matching plain blue used for missing original cloth; no recovered floral detail claimed.'}
if not source_only:(ROOT/'reports/back_repair_validation.json').write_text(json.dumps(report,indent=2))
print('BACK_PATCHES_VALIDATED',len(checks),'regions/LODs',len(unchanged),'unchanged source meshes')
