"""Bounded CPU skirt-cage diagnostic; not the Bannerlord solver."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from workspace_paths import workspace_root
sys.path.insert(0, str(workspace_root(Path(__file__).resolve().parents[1])/'tools/cloth_compiler'))
from cloth_payload import read,decode_positions
from mapping_payload import read as read_map,reconstruct

def probe(root):
    cfg=json.loads((root/'tools/model_config.json').read_text());cfg['mapped_cloth']=json.loads((root/'tools/skirt_proxy_config.json').read_text());prefix=cfg.get('prefix','yqs');b=root/'build';workspace=next(p for p in root.parents if (p/'tools/asset_helpers').is_dir())
    sys.path.insert(0,str(workspace/'tools/asset_helpers/previewer'))
    from baker.skeleton import parse_skeljson
    from baker.animation import parse_animjson,skin_matrices,lbs
    rig=parse_skeljson(json.loads((root/'reports/final_skeleton.json').read_text()));anim=parse_animjson(json.loads((root/'reports/ui_neutral_female.json').read_text()));skin=skin_matrices(rig,anim,max(1,anim['start']))
    inspected=json.loads((b/'mapped_final/inspection.json').read_text());proxy=next(m for m in inspected if m['Name']==prefix+'_cloth_proxy');d=read(Path(proxy['segments'][0]['path']))
    source=json.loads((b/'proxy_source.json').read_text());cage_render=source.get('skirt_vertices',list(range(cfg['mapped_cloth']['columns']*cfg['mapped_cloth']['rings'])));cage=d['render_to_sim'][cage_render];cage_mask=np.zeros(d['vertex_count'],bool);cage_mask[cage]=True
    bi=d['bone_indices'].reshape(-1,4);bw=np.rint(d['bone_weights'].reshape(-1,4)*255).astype(int);rest=lbs(decode_positions(d),bi,bw,skin);travel=d['max_distances'];active=cage_mask&(travel>0);ids=np.flatnonzero(active)
    caps=json.loads((root/'reports/cloth_collision.json').read_text())['capsules'];posed=[]
    for c in caps:
        endpoints=[]
        for k,(point,bone) in enumerate(zip(c['endpoints_m'],c['bones'])):
            weights=c.get('endpoint_weights',[[dict(bone=n,weight=1.)] for n in c['bones']])[k];p=np.zeros(3)
            for influence in weights:
                matrix=skin[rig['names'].index(influence['bone'])];p+=influence['weight']*(matrix[:3,:3]@point+matrix[:3,3])
            endpoints.append(p)
        posed.append((np.array(endpoints),c['radius_m']))
    def gap(points):
        result=np.full(len(points),100.)
        for (a,z),radius in posed:
            axis=z-a;t=np.clip((points-a)@axis/(axis@axis),0,1);result=np.minimum(result,np.linalg.norm(points-a-t[:,None]*axis,axis=1)-radius)
        return result
    root_overlap=np.maximum(-gap(rest[cage_mask&~active]),0);assert root_overlap.max()<.006,('Cage fixed root collision',root_overlap.max())
    groups=[]
    for group in d['constraint_sets']:
        for kind,(start,count) in enumerate(group.reshape(4,2)):
            edges=d['constraints'][start:start+count];keep=cage_mask[edges].all(1);edges=edges[keep];length=d['rest_lengths'][start:start+count][keep]
            if len(edges):groups.append((edges[:,0],edges[:,1],length,1. if kind==0 else .3))
    x=rest.copy();velocity=np.zeros_like(x);anchor=d['anchors']>>16;anchor_max=(d['anchors']&65535)*d['anchor_scale']
    for step in range(120):
        previous=x.copy();velocity[active,2]-=9.81/60;x[active]+=velocity[active]/60
        for iteration in range(10):
            for i,j,length,stiffness in groups:
                delta=x[j]-x[i];dist=np.linalg.norm(delta,axis=1);correction=delta*((dist-length)/np.maximum(dist,1e-10)/np.maximum(active[i].astype(float)+active[j],1)*stiffness)[:,None]
                x[i]+=correction*active[i,None];x[j]-=correction*active[j,None]
            delta=x[ids]-x[anchor[ids]];distance=np.linalg.norm(delta,axis=1);hit=distance>anchor_max[ids];h=ids[hit]
            x[h]-=delta[hit]/distance[hit,None]*(distance[hit]-anchor_max[h])[:,None]*.8
            moving=x[ids].copy()
            for (a,z),radius in posed*4:
                axis=z-a;t=np.clip((moving-a)@axis/(axis@axis),0,1);delta=moving-a-t[:,None]*axis;distance=np.linalg.norm(delta,axis=1);hit=distance<radius
                moving[hit]+=delta[hit]/np.maximum(distance[hit,None],1e-10)*(radius-distance[hit])[:,None]
            delta=moving-rest[ids];dist=np.linalg.norm(delta,axis=1);x[ids]=rest[ids]+delta*np.minimum(1,travel[ids]/np.maximum(dist,1e-10))[:,None]
            x[~active]=rest[~active]
        velocity=(x-previous)*60*.92
    tri=d['render_to_sim'][np.array(source['indices']).reshape(-1,3)];normals=np.zeros_like(x);cross=np.cross(x[tri[:,1]]-x[tri[:,0]],x[tri[:,2]]-x[tri[:,0]]);np.add.at(normals,tri.ravel(),np.repeat(cross,3,axis=0));size=np.linalg.norm(normals,axis=1);normal_valid=size>1e-10;normals[normal_valid]/=size[normal_valid,None]
    raw=d['rest_normals'];fallback=np.column_stack([raw>>21,(raw>>10)&2047,raw&1023])/np.array([2047,2047,1023])*2-1;fallback/=np.linalg.norm(fallback,axis=1)[:,None];normals[~normal_valid]=fallback[~normal_valid]
    plans={p['guid']:p for p in json.loads((b/'mapped_render_maps/manifest.json').read_text())};layer_rows=[]
    for path in (b/'cloth_final').glob('*.mesh.json'):
        m=json.loads(path.read_text())
        if m['lod']!=0:continue
        plan=plans[m['guid']];i,w=read_map(Path(plan['path']).read_bytes());mapped=np.array(m['alpha'])>0;mapped[plan['unmapped_vertices']]=False;skirt=mapped&cage_mask[i].all(1)
        if not skirt.any():continue
        base=lbs(np.array(m['positions']),np.array(m['bones']),np.array(m['weights']),skin);after=base.copy();after[skirt]=reconstruct(x,normals,i[skirt],w[skirt])
        # Layer offsets are shared-driver coordinates, not independent solver states.
        np.savez_compressed(b/(m['name']+'_mapped_settled.npz'),before=base,after=after,indices=m['indices'])
        minimum=-.026 if cfg['mapped_cloth'].get('method')=='linked_surfaces' else -.003
        assert w[skirt,3].min()>minimum,('Excessive common-surface offset',m['name'],w[skirt,3].min())
        layer_rows.append(dict(mesh=m['name'],mapped_skirt_vertices=int(skirt.sum()),minimum_offset_m=float(w[skirt,3].min()),mean_vertical_change_m=float((after[skirt,2]-base[skirt,2]).mean()),raised_fraction=float(((after[skirt,2]-base[skirt,2])>.01).mean())))
    residual=np.maximum(-gap(x[ids]),0);assert residual.max()<.02,('Cage collision residual',residual.max())
    assert np.isfinite(x).all() and np.array_equal(x[~active],rest[~active]);assert np.max(np.linalg.norm(x-rest,axis=1)-travel)<1e-6
    report=dict(status='pass',candidate_sha256=hashlib.sha256((b/'mapped_candidate.tpac').read_bytes()).hexdigest(),fixed_root_overlap_m=float(root_overlap.max()),fixed_root_drift_m=0.,cage_max_residual_m=float(residual.max()),cage_p99_residual_m=float(np.percentile(residual,99)),layers=layer_rows,scope='120 CPU gravity steps; 10 grouped iterations, soft geodesic anchors and repeated capsule projection; skirt cage only; non-skirt islands held at skinning reference',layer_self_collision_supported=False,game_solver_used=False,game_verified=False)
    (root/'reports/mapped_settling_validation.json').write_text(json.dumps(report,indent=2));print('MAPPED_CAGE_PROBE',root.name,report)

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    try:
        probe(root)
    except AssertionError as error:
        report=dict(status='fail',reason=str(error),candidate_sha256=hashlib.sha256((root/'build/mapped_candidate.tpac').read_bytes()).hexdigest(),game_solver_used=False,game_verified=False)
        (root/'reports/mapped_settling_validation.json').write_text(json.dumps(report,indent=2))
        raise
