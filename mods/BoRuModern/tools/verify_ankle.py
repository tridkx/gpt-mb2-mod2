"""Measure final-package ankle overlap in the moving foot's bind frame."""
import sys,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[1]
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
from georead import read_geo
a=np.load(ROOT/'build/fitted_model.npz')
def rim_points():
    p=a['boru_legs_cloth_p'];u,inv=np.unique(np.round(p,4),axis=0,return_inverse=True);f=inv[a['boru_legs_cloth_f']]
    edges=Counter(tuple(sorted((i,j))) for tri in f for i,j in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]);adj=defaultdict(set)
    for (i,j),n in edges.items():
        if n==1:adj[i].add(j);adj[j].add(i)
    seen=set();rings=[]
    for i in adj:
        if i in seen:continue
        todo=[i];component=[]
        while todo:
            j=todo.pop()
            if j in seen:continue
            seen.add(j);component.append(j);todo.extend(adj[j]-seen)
        q=u[component]
        if len(q)>=10 and q[:,2].mean()>.16:rings.append(q)
    assert len(rings)==2
    return {side:min(rings,key=lambda q:float(q[:,0].mean())*(1 if side=='l' else -1)) for side in ['l','r']}
rim=rim_points();bottom=a['boru_legs_skin_p'];bottom=bottom[bottom[:,2]<.13];assert len(bottom)>12
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));rows=[]
for lod in range(4):
    meshes=[m for p in (ROOT/'build'/f'final_export_lod{lod}'/'geo').glob('*.bin') for m in read_geo(p)]
    groups={}
    for base in ['boru_legs_skin','boru_legs_cloth']:
        ms=[m for m in meshes if m['name'].split('.lod')[0].split('.b')[0]==base]
        groups[base]={key:np.concatenate([m[key] for m in ms]) for key in ['pos','bi','bw']}
    references={}
    for side in ['l','r']:
        b=bottom[bottom[:,0]<0 if side=='l' else bottom[:,0]>0];references[side]={}
        for name,points in [('boru_legs_skin',b),('boru_legs_cloth',rim[side])]:
            m=groups[name];distance,ids=cKDTree(m['pos']).query(points);assert distance.max()<.00015
            references[side][name]={key:m[key][ids] for key in ['pos','bi','bw']}
    for label in ['idle','run','bow','riding']:
        anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));minimum=1e9;worst=None
        for frame in range(max(1,anim['start']),anim['frames']):
            skin=skin_matrices(rig,anim,frame)
            for side in ['l','r']:
                inverse=np.linalg.inv(skin[rig['names'].index(side+'_foot')]);rest={}
                for name,m in references[side].items():
                    posed=lbs(m['pos'],m['bi'],m['bw'],skin);rest[name]=posed@inverse[:3,:3].T+inverse[:3,3]
                overlap=float(rest['boru_legs_cloth'][:,2].min()-rest['boru_legs_skin'][:,2].max())
                if overlap<minimum:minimum=overlap;worst={'frame':frame,'side':side}
        assert minimum>.02,(lod,label,minimum,worst)
        rows.append({'lod':lod,'motion':label,'frames_checked':anim['frames']-max(1,anim['start']),'minimum_overlap_m':minimum,'worst':worst})
package=ROOT/'module/BoRuModern/AssetPackages/boru.tpac'
report={'status':'pass','version':'v1.0.2','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'hidden_source_cut_extension_m':.045,'measurement':'Sock opening minimum height minus hidden skin-cut maximum height in moving foot bind frame; final quantized weights, all frames and all LODs','motions':rows,'limitations':'Axial overlap is a seam coverage guard, not a complete surface intersection or game IK test.'}
(ROOT/'reports/ankle_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
