from workspace_paths import workspace_root
"""Offline PBD gravity probe with final constraints, fixed roots and travel limits.

This diagnostic is not Bannerlord's solver and cannot certify game collision.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'build';sys.path.insert(0,str(workspace_root(R)/'tools'))
from cloth_compiler.cloth_payload import read
from pelvis_support import clearance
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules']
plans=json.loads((B/'cooked_cloth/manifest.json').read_text());rows=[]
for plan in plans:
    if plan['lod']!=0 or not plan['mesh'].startswith('yqs_part_10'):continue
    stem=plan['metamesh']+'_'+plan['guid'];mesh=json.loads((B/'cloth_final'/(stem+'.mesh.json')).read_text())
    d=read(B/'cloth_final'/(stem+'.bin'));mapping=d['render_to_sim'];nv=d['vertex_count']
    rest=np.zeros((nv,3));rest[mapping]=np.array(mesh['positions']);travel=d['max_distances'];active=travel>0
    edges=d['constraints'];length=d['rest_lengths'];i,j=edges.T
    denom=active[i].astype(float)+active[j];denom=np.maximum(denom,1)
    degree=np.bincount(edges.ravel(),minlength=nv);degree=np.maximum(degree,1)
    x=rest.copy();velocity=np.zeros_like(x)
    # Material-like damping and gravity; Jacobi relaxation of the actual
    # compiled edges. Fixed roots are never collision-projected.
    for step in range(120):
        previous=x.copy();velocity[active,2]-=9.81/60;x[active]+=velocity[active]/60
        for iteration in range(12):
            delta=x[j]-x[i];dist=np.linalg.norm(delta,axis=1)
            correction=delta*((dist-length)/np.maximum(dist,1e-10)/denom)[:,None]
            update=np.stack([np.bincount(i,weights=correction[:,c],minlength=nv)-np.bincount(j,weights=correction[:,c],minlength=nv) for c in range(3)],axis=1)
            x[active]+=.8*update[active]/degree[active,None]
            for cap in caps:
                a,b=np.array(cap['endpoints_m']);axis=b-a;t=np.clip((x-a)@axis/(axis@axis),0,1)
                delta=x-a-t[:,None]*axis;distance=np.linalg.norm(delta,axis=1);hit=(distance<cap['radius_m'])&active
                x[hit]+=delta[hit]/np.maximum(distance[hit,None],1e-10)*(cap['radius_m']-distance[hit])[:,None]
            delta=x-rest;dist=np.linalg.norm(delta,axis=1);x=rest+delta*np.minimum(1,travel/np.maximum(dist,1e-10))[:,None]
            x[~active]=rest[~active]
        velocity=(x-previous)*60*.92
    hip=active&(abs(rest[:,0])<.20)&(rest[:,2]>.82)&(rest[:,2]<1.14)
    residual=np.maximum(-clearance(x[hip],caps),0) if hip.any() else np.array([0.])
    assert np.isfinite(x).all() and np.array_equal(x[~active],rest[~active])
    assert np.max(np.linalg.norm(x-rest,axis=1)-travel)<1e-6
    assert residual.max()<.002, ('Static hip collision conflict exceeds 2 mm',plan['mesh'],residual.max())
    rows.append(dict(mesh=plan['mesh'],hip_particles=int(hip.sum()),max_capsule_residual_m=float(residual.max()),p99_capsule_residual_m=float(np.percentile(residual,99)),fixed_root_drift_m=0,max_travel_exceeded_m=0))
    np.savez_compressed(B/(plan['mesh']+'_settled_probe.npz'),positions=x[mapping],indices=mesh['indices'])
report=dict(status='pass',scope='120 steps at 60 Hz, 12 Jacobi iterations; final compiled edges, gravity, capsule projection and travel clamp; not Bannerlord physics',final_package_sha256=hashlib.sha256((R/'module/YueQingShuRace/AssetPackages/yqs.tpac').read_bytes()).hexdigest(),meshes=rows,game_solver_used=False)
(R/'reports/settled_skirt_probe.json').write_text(json.dumps(report,indent=2));print('SETTLED_SKIRT_PROBE',rows)
