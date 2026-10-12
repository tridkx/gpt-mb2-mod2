"""Static gravity/constraint proxy of the captured creation pose, not the engine."""
import json,sys,numpy as np,hashlib
from collision_helpers import R,W,rig,native_skins,endpoints,published_capsules
sys.path.insert(0,str(W/'tools'))
from cloth_compiler.cloth_payload import read
from baker.animation import lbs
from georead import read_geo
skin=next(s for label,frame,s in native_skins() if label=='captured_creation' and frame==7)
caps=published_capsules()
posed_caps=[(*endpoints(c,skin),c['radius_m']) for c in caps]
render=[g for path in (R/'build/final_export_lod0/geo').glob('*.bin') for g in read_geo(path) if g['name'].startswith('txgirl2_part_')]
result={g['name']:lbs(g['pos'],g['bi'],g['bw'],skin) for g in render};rows=[]
for file in (R/'build/cloth_final').glob('*.mesh.json'):
    m=json.loads(file.read_text())
    if m['lod']!=0:continue
    d=read(file.with_name(file.name.replace('.mesh.json','.bin')));mapping=d['render_to_sim'];nv=d['vertex_count'];start=d['simulation_start'];active=np.arange(start,nv)
    reference=np.zeros((nv,3));reference[mapping]=lbs(np.array(m['positions']),np.array(m['bones']),np.array(m['weights']),skin)
    positions=reference.copy();previous=positions.copy();root=(d['anchors']>>16);length=(d['anchors']&65535)*d['anchor_scale'];maxdist=d['max_distances'];constraints=d['constraints'];sets=d['constraint_sets'];stiffness=np.zeros(len(constraints))
    for row in sets:
        for kind,value in [(0,1),(1,.9),(2,.2),(3,1)]:stiffness[row[kind*2]:row[kind*2]+row[kind*2+1]]=value
    def limit():
        delta=positions[active]-reference[active];dist=np.linalg.norm(delta,axis=1);positions[active]=reference[active]+delta*np.minimum(1,maxdist[active]/np.maximum(dist,1e-9))[:,None]
    for frame in range(180):
        velocity=(positions-previous)*.7;previous=positions.copy();positions[active]+=velocity[active]+[0,0,-9.81/3600];limit()
        for iteration in range(6):
            delta=positions[active]-positions[root[active]];dist=np.linalg.norm(delta,axis=1);positions[active]-=delta*(np.maximum(dist-length[active],0)/np.maximum(dist,1e-9))[:,None]
            for row in sets:
                begin=row[0];end=row[6]+row[7];c=constraints[begin:end];a,b=c.T;delta=positions[b]-positions[a];dist=np.linalg.norm(delta,axis=1);mass_a=(a>=start).astype(float);mass_b=(b>=start).astype(float);mass=mass_a+mass_b
                correction=delta*((dist-d['rest_lengths'][begin:end])/np.maximum(dist,1e-9)*stiffness[begin:end]/np.maximum(mass,1))[:,None]
                positions[a]+=correction*mass_a[:,None];positions[b]-=correction*mass_b[:,None]
            limit()
            for a,b,radius in posed_caps:
                q=positions[active];v=b-a;t=np.clip((q-a)@v/max(v@v,1e-10),0,1);center=a+t[:,None]*v;delta=q-center;dist=np.linalg.norm(delta,axis=1)
                positions[active]=center+delta*(np.maximum(dist,radius)/np.maximum(dist,1e-9))[:,None]
            positions[:start]=reference[:start]
    displacement=np.linalg.norm(positions-reference,axis=1);c=constraints;ratio=np.linalg.norm(positions[c[:,1]]-positions[c[:,0]],axis=1)/d['rest_lengths'];assert np.isfinite(positions).all()
    fixed_drift=float(displacement[:start].max());assert fixed_drift<1e-9
    rows.append(dict(mesh=m['name'],frames=180,fixed_root_drift_m=fixed_drift,maximum_displacement_m=float(displacement.max()),p99_stretch_ratio=float(np.percentile(ratio[stiffness==1],99)),scope='180 fixed-pose frames; point capsule projection, stretch/bend/anchor constraints and displacement clamp; virtual triangle collisions/wind/inertia excluded; not engine proof'))
    result[m['name']]=positions[mapping]
np.savez_compressed(R/'build/cloth_proxy_creation.npz',**result)
(R/'reports/static_cloth_proxy.json').write_text(json.dumps(dict(status='pass_proxy_completed',final_package_sha256=hashlib.sha256((R/'module/TianxiangGirlT2Race/AssetPackages/txgirl2.tpac').read_bytes()).hexdigest(),collision_xml_sha256=hashlib.sha256((R/'module/TianxiangGirlT2Race/ModuleData/cloth_bodies.xml').read_bytes()).hexdigest(),version=json.loads((R/'tools/model_config.json').read_text())['version'],pose='Actual captured creation pose index 7',game_cloth_solver_used=False,meshes=rows),indent=2))
print('STATIC_CLOTH_PROXY_READY',rows)
