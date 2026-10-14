"""Check source layer order in final native mapping and CPU motion tracks.

Pairs are sampled by common skirt angle/height. This is a layer-order probe,
not continuous triangle self collision or a guarantee of zero penetration.
"""
from pathlib import Path
import json,sys,hashlib,numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path.insert(0,str(W/'tools/cloth_compiler'))
from cloth_payload import read,decode_positions
from mapping_payload import read as read_mapping,reconstruct

def main():
    b=R/'build';source=json.loads((b/'proxy_source.json').read_text())
    inspect=json.loads((b/'mapped_final/inspection.json').read_text())
    proxy=next(x for x in inspect if x['Name']=='yqs_cloth_proxy')
    body=next(x for x in inspect if x['Name']=='yqs_body')
    d=read(Path(proxy['segments'][0]['path']));cage=np.unique(d['render_to_sim'][source['skirt_vertices']])
    mask=np.zeros(d['vertex_count'],bool);mask[cage]=True
    tri=d['render_to_sim'][np.array(source['indices']).reshape(-1,3)];tri=tri[mask[tri].all(1)]
    render=next(json.loads(p.read_text()) for p in (b/'cloth_final').glob('*.mesh.json') if json.loads(p.read_text())['name']=='yqs_part_10')
    segment=next(s for s in body['segments'] if s['OwnerGuid']==render['guid'])
    i,w=read_mapping(Path(segment['path']).read_bytes())
    active=np.array(render['alpha'])>0;assert mask[i[active]].all()
    assert np.maximum(-w[active,:3],0).max()<.02, 'Skirt maps outside coherent chart'
    p=np.array(render['positions']);cfg=json.loads((R/'tools/outer_driver_config.json').read_text());center=np.array(cfg['center_xy'])
    raw=np.load(b/'fitted_model.npz');sp=raw['yqs_part_10_p'];q,owner=np.unique(sp,axis=0,return_inverse=True);f=owner[raw['yqs_part_10_f']]
    e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(e)),e.T),shape=(len(q),len(q))),directed=False)
    nearest=cKDTree(sp).query(p)[1];layer=labels[owner[nearest]]
    primary=json.loads((b/'outer_driver.json').read_text())['source_component']
    base=np.flatnonzero(active&(layer==primary))
    radius=np.linalg.norm(p[:,:2]-center,axis=1);theta=np.arctan2(p[:,1]-center[1],p[:,0]-center[0])
    chart=np.column_stack([np.cos(theta)*.16,np.sin(theta)*.16,p[:,2]])
    pairs=[];pair_layers=[]
    for part in np.unique(layer[active]):
        if part==primary:continue
        ids=np.flatnonzero(active&(layer==part));distance,near=cKDTree(chart[base]).query(chart[ids]);other=base[near]
        gap=radius[ids]-radius[other]
        keep=(distance<.012)&(abs(gap)>.004)
        pairs.extend(zip(other[keep],ids[keep]));pair_layers.extend([int(part)]*int(keep.sum()))
    pairs=np.array(pairs,int);assert len(pairs)>20,'Too few overlapping layer pairs'
    a,z=pairs.T;sign=np.sign(radius[z]-radius[a]);baseline=abs(radius[z]-radius[a])
    tracks=[]
    motion_report=json.loads((R/'reports/simplified_skirt_motion.json').read_text())
    candidate_hash=hashlib.sha256((b/'mapped_candidate.tpac').read_bytes()).hexdigest()
    assert motion_report['candidate_sha256']==candidate_hash
    for entry in motion_report['motions']:
        name=entry['motion'];track=np.load(b/'simplified_skirt_motion'/name/'frames.npz');positions=track['positions'];rows=[]
        for frame,points in enumerate(positions):
            x=np.zeros((d['vertex_count'],3));x[cage]=points;normals=np.zeros_like(x)
            cross=np.cross(x[tri[:,1]]-x[tri[:,0]],x[tri[:,2]]-x[tri[:,0]])
            np.add.at(normals,tri.ravel(),np.repeat(cross,3,axis=0));normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
            after=reconstruct(x,normals,i,w)
            direction=(normals[i[a]]*w[a,:3,None]).sum(1);direction/=np.maximum(np.linalg.norm(direction,axis=1)[:,None],1e-12)
            gap=np.sum((after[z]-after[a])*direction,axis=1)*sign
            rows.append(dict(frame=frame,min_ordered_gap_m=float(gap.min()),inverted_pairs=int((gap<-.002).sum()),
                close_pairs=int((gap<.001).sum()),p10_gap_m=float(np.percentile(gap,10))))
        tracks.append(dict(motion=name,frames=len(rows),worst_inverted_pairs=max(row['inverted_pairs'] for row in rows),
            minimum_ordered_gap_m=min(row['min_ordered_gap_m'] for row in rows),per_frame=rows))
    report=dict(status='within_sampled_layer_order' if all(x['worst_inverted_pairs']==0 for x in tracks) else 'needs_review',
        candidate_sha256=candidate_hash,source_pairs=len(pairs),source_layer_ids=sorted(set(pair_layers)),
        minimum_source_radial_gap_m=float(baseline.min()),independent_inner_simulation_vertices=0,
        motion_scope=tracks,minor_penetration_tolerance_m=.002,
        continuous_self_collision_supported=False,game_verified=False,
        scope='Angle/height nearest source layer pairs in LOD0; final TPAC mapping and CPU skirt trajectories')
    output=R/'reports/experiments/outer_driven_layers_2026-10-14/layer_order_validation.json'
    output.write_text(json.dumps(report,indent=2));print('LAYER_ORDER',report['status'],len(pairs),[(r['motion'],r['worst_inverted_pairs']) for r in tracks])

if __name__=='__main__':main()
