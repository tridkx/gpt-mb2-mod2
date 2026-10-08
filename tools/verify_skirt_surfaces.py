"""Final TPAC skirt vs actual delivered leg/shoe surfaces, every motion frame."""
import bpy,sys,json,re
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[sys.argv.index('--')+1]
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'));sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
fit=json.loads((ROOT/'reports/rig_fit.json').read_text());skirts={r['object'] for r in fit['parts'] if r['kind']=='skirt'};legs={r['object'] for r in fit['parts'] if r['part']=='legs'}
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));results=[]
trial='fit' in sys.argv
for lod in ([0] if trial else range(4)):
    folder=ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')/'geo';meshes=[m for f in folder.glob('*.bin') for m in read_geo(f)]
    cloth=[m for m in meshes if re.sub(r'\.lod\d+$','',m['name']) in skirts];body=[m for m in meshes if re.sub(r'\.lod\d+$','',m['name']) in legs]
    if trial:
        from mathutils.kdtree import KDTree
        baseline=ROOT/'build/repair_baseline_v1.0.0';old=np.load(baseline/'rig_arrays.npz');fitted=np.load(ROOT/'build/skirt_clearance_fit.npz')
        cloth=[m for f in (baseline/'export/geo').glob('*.bin') for m in read_geo(f) if m['name'] in skirts]
        for m in cloth:
            points=old[m['name']+'_P'];kd=KDTree(len(points))
            for index,p in enumerate(points):kd.insert(p,index)
            kd.balance();vi=np.array([kd.find(p)[1] for p in m['pos']]);m['pos']=fitted['P'][vi];w=fitted['W'][vi];m['bi']=np.argsort(-w,axis=1)[:,:4];m['bw']=np.take_along_axis(w,m['bi'],axis=1)*255
            m['pos']=fitted['P'];w=fitted['W'];m['bi']=np.argsort(-w,axis=1)[:,:4];m['bw']=np.take_along_axis(w,m['bi'],axis=1)*255;m['idx']=np.array(json.loads((ROOT/'build/skirt_triangles.json').read_text())).ravel()
    for label in ['run','bow','riding','idle']:
        anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));frames=list(range(max(1,anim['start']),anim['frames'])) if label!='idle' else sorted(set(np.linspace(1,anim['frames']-1,16).astype(int).tolist()))
        maximum=0;worst=0;badframes=0
        for frame in frames:
            skin=skin_matrices(rig,anim,frame);points=[];faces=[];off=0
            for m in body:
                p=lbs(m['pos'],m['bi'],m['bw'],skin);points.extend(p.tolist());faces.extend((m['idx'].reshape(-1,3)+off).tolist());off+=len(p)
            bodytree=BVHTree.FromPolygons(points,faces,all_triangles=True,epsilon=0)
            count=0
            for m in cloth:
                p=lbs(m['pos'],m['bi'],m['bw'],skin);tree=BVHTree.FromPolygons(p.tolist(),m['idx'].reshape(-1,3).tolist(),all_triangles=True,epsilon=0);count+=len(tree.overlap(bodytree))
            if count:badframes+=1
            if count>maximum:maximum=count;worst=frame
        results.append({'lod':lod,'motion':label,'frames':len(frames),'max_overlapping_triangle_pairs':maximum,'worst_frame':worst,'frames_with_overlap':badframes});print(results[-1],flush=True)
report={'scope':'final TPAC actual delivered skirt and leg/shoe triangle surfaces; BVH overlap; no cloth solver','status':'pass' if all(r['max_overlapping_triangle_pairs']==0 for r in results) else 'needs_review','results':results,'game_verified':False}
(ROOT/('build/skirt_surface_trial.json' if trial else 'reports/skirt_surface_validation.json')).write_text(json.dumps(report,indent=2));print('SKIRT_SURFACE_VALIDATION',report['status'])
