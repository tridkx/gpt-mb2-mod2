"""Compare actual layer triangle crossings in old/new CPU mapped trajectories.

Run in Blender for BVH broad phase. Exact edge/triangle tests exclude grazing
contacts below 1 mm; this is sampled CPU motion, not game self collision.
"""
from pathlib import Path
import sys,json,numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path[:0]=[str(W/'tools/cloth_compiler'),str(W/'tools/asset_helpers/previewer')]
from cloth_payload import read
from mapping_payload import read as read_map,reconstruct
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs

def source_layers(p):
    raw=np.load(R/'build/fitted_model.npz');sp=raw['yqs_part_10_p'];q,inv=np.unique(sp,axis=0,return_inverse=True);f=inv[raw['yqs_part_10_f']]
    parent=np.arange(len(q))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,b in np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    _,labels=np.unique([find(i) for i in range(len(q))],return_inverse=True)
    tree=KDTree(len(sp))
    for i,point in enumerate(sp):tree.insert(point,i)
    tree.balance()
    return np.array([labels[inv[tree.find(point)[1]]] for point in p])

def edge_hits(a,b):
    found=np.zeros(len(a),bool)
    e1=b[:,1]-b[:,0];e2=b[:,2]-b[:,0]
    for j in range(3):
        start=a[:,j];direction=a[:,(j+1)%3]-start
        h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h)
        good=abs(det)>1e-12;reciprocal=np.zeros(len(a));reciprocal[good]=1/det[good]
        s=start-b[:,0];u=np.einsum('ij,ij->i',s,h)*reciprocal
        q=np.cross(s,e1);v=np.einsum('ij,ij->i',direction,q)*reciprocal
        t=np.einsum('ij,ij->i',e2,q)*reciprocal
        margin=.001/np.maximum(np.linalg.norm(direction,axis=1),1e-12)
        found|=good&(u>1e-5)&(v>1e-5)&(u+v<1-1e-5)&(t>margin)&(t<1-margin)
    return found

def crossings(points,faces_by_layer):
    keys=list(faces_by_layer);trees={k:BVHTree.FromPolygons(points.tolist(),faces_by_layer[k].tolist(),all_triangles=True) for k in keys}
    rows=[]
    for j,a in enumerate(keys):
        for b in keys[j+1:]:
            pairs=np.array(trees[a].overlap(trees[b]),int)
            if not len(pairs):rows.append(dict(layers=[int(a),int(b)],pairs=0));continue
            ta=points[faces_by_layer[a][pairs[:,0]]];tb=points[faces_by_layer[b][pairs[:,1]]]
            na=np.cross(ta[:,1]-ta[:,0],ta[:,2]-ta[:,0]);nb=np.cross(tb[:,1]-tb[:,0],tb[:,2]-tb[:,0])
            na/=np.maximum(np.linalg.norm(na,axis=1)[:,None],1e-12);nb/=np.maximum(np.linalg.norm(nb,axis=1)[:,None],1e-12)
            da=np.einsum('nvc,nc->nv',ta-tb[:,0,None,:],nb)
            db=np.einsum('nvc,nc->nv',tb-ta[:,0,None,:],na)
            # Require more than 1 mm straddling on at least one surface;
            # shared seams, coplanar contacts and shallow grazes are excluded.
            deep=((da.min(1)<-.001)&(da.max(1)>.001))|((db.min(1)<-.001)&(db.max(1)>.001))
            hit=deep&(edge_hits(ta,tb)|edge_hits(tb,ta))
            rows.append(dict(layers=[int(a),int(b)],pairs=int(hit.sum())))
    return sum(x['pairs'] for x in rows),rows

def main():
    current=R/'build';previous=current/'experiments/simplified_primary_surface_964'
    render=next(json.loads(p.read_text()) for p in (current/'cloth_final').glob('*.mesh.json') if json.loads(p.read_text())['name']=='yqs_part_10')
    p=np.array(render['positions']);faces=np.array(render['indices']).reshape(-1,3);layer=source_layers(p)
    paint=next(x for x in json.loads((R/'reports/cloth_paint.json').read_text()) if x['object']=='yqs_part_10')
    parts=[x['component'] for x in paint['components'] if x['kind']=='skirt']
    split={c:faces[(layer[faces]==c).all(1)] for c in parts};assert all(len(x) for x in split.values())
    rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));results=[]
    for label,b in [('previous_964',previous),('coherent_outer',current)]:
        inspect=json.loads((b/'mapped_final/inspection.json').read_text())
        proxy=next(x for x in inspect if x['Name']=='yqs_cloth_proxy');body=next(x for x in inspect if x['Name']=='yqs_body')
        def segment_path(s):return b/'mapped_final'/Path(s['path']).name
        d=read(segment_path(proxy['segments'][0]));source=json.loads((b/'proxy_source.json').read_text())
        cage=np.unique(d['render_to_sim'][source['skirt_vertices']]);mask=np.zeros(d['vertex_count'],bool);mask[cage]=True
        tri=d['render_to_sim'][np.array(source['indices']).reshape(-1,3)];tri=tri[mask[tri].all(1)]
        seg=next(x for x in body['segments'] if x['OwnerGuid']==render['guid']);i,w=read_map(segment_path(seg).read_bytes())
        active=np.array(render['alpha'])>0;active&=mask[i].all(1)
        summaries=[]
        for name in ['ui_neutral_female','run','riding']:
            track=np.load(b/'simplified_skirt_motion'/name/'frames.npz');anim=parse_animjson(json.loads((R/'reports'/(name+'.json')).read_text()))
            rows=[]
            for frame,points in enumerate(track['positions']):
                skin=skin_matrices(rig,anim,frame+anim['start']);after=lbs(p,np.array(render['bones']),np.array(render['weights']),skin)
                x=np.zeros((d['vertex_count'],3));x[cage]=points;normals=np.zeros_like(x)
                cross=np.cross(x[tri[:,1]]-x[tri[:,0]],x[tri[:,2]]-x[tri[:,0]])
                np.add.at(normals,tri.ravel(),np.repeat(cross,3,axis=0));normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
                after[active]=reconstruct(x,normals,i[active],w[active])
                count,detail=crossings(after,split)
                rows.append(dict(source_frame=frame+anim['start'],crossing_triangle_pairs=count,layer_pairs=detail))
            entry=dict(motion=name,frames=len(rows),maximum_crossing_triangle_pairs=max(x['crossing_triangle_pairs'] for x in rows),
                       mean_crossing_triangle_pairs=float(np.mean([x['crossing_triangle_pairs'] for x in rows])),per_frame=rows)
            summaries.append(entry);print('CROSSINGS',label,name,entry['maximum_crossing_triangle_pairs'],flush=True)
        results.append(dict(candidate=label,motions=summaries))
    report=dict(scope='LOD0 four source skirt components; all saved CPU motion frames; exact edge/triangle intersection after BVH broad phase',
                grazing_tolerance_m=.001,continuous_collision_supported=False,game_verified=False,results=results)
    (R/'reports/experiments/outer_driven_layers_2026-10-14/layer_crossing_comparison.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
