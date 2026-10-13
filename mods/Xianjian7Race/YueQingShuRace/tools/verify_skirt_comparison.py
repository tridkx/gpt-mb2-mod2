"""Compare collision pressure, real fixed roots and constrained gravity settling."""
from pathlib import Path
import sys,json,subprocess,hashlib
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
from pelvis_support import clearance,pose_capsule
R=Path(__file__).resolve().parents[1];W=workspace_root(R);B=R/'build';cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));prefix='yqs'
sys.path[:0]=[str(W/'tools'),str(W/'tools/asset_helpers/previewer')]
from cloth_compiler.cloth_payload import read
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
old=json.loads((R/'reports/history/v0.3.1/cloth_collision.json').read_text())['capsules'];new=json.loads((R/'reports/cloth_collision.json').read_text())['capsules']
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));anim=parse_animjson(json.loads((R/'reports/idle.json').read_text()));skin=skin_matrices(rig,anim,max(1,anim['start']))
old_pose=[dict(c,endpoints_m=pose_capsule(c,skin,rig['names']).tolist()) for c in old];new_pose=[dict(c,endpoints_m=pose_capsule(c,skin,rig['names']).tolist()) for c in new]
import zipfile
with zipfile.ZipFile(R/'dist/YueQingShuRace_v0.3.1_Mod.zip') as archive:
 (B/'baseline_v0.3.1.tpac').write_bytes(archive.read('YueQingShuRace/AssetPackages/yqs.tpac'))
dump=B/'baseline_cloth';dump.mkdir(exist_ok=True)
subprocess.run(['dotnet',str(B/'cloth_probe/NativeClothProbe.dll'),str(B/'baseline_v0.3.1.tpac'),prefix+'_body','--dump-segments',str(dump)],check=True,stdout=subprocess.DEVNULL)
skirt_names={r['object'] for r in json.loads((R/'reports/cloth_paint.json').read_text()) if any(c['kind']=='skirt' for c in r['components'])}
height=1.18

def settle(rest,d,caps):
 active=d['max_distances']>0;ids=np.flatnonzero(active);travel=d['max_distances'];edges=d['constraints'];i,j=edges.T;length=d['rest_lengths'];denom=np.maximum(active[i].astype(float)+active[j],1);degree=np.maximum(np.bincount(edges.ravel(),minlength=len(rest)),1)
 x=rest.copy();velocity=np.zeros_like(x)
 for step in range(120):
  before=x.copy();velocity[active,2]-=9.81/60;x[active]+=velocity[active]/60
  for iteration in range(10):
   # Use cooked disjoint batches, avoiding the artificial softness of degree-averaged Jacobi updates.
   for group in d['constraint_sets']:
    for kind,(start,count) in enumerate(group.reshape(4,2)):
     if not count:continue
     gi,gj=edges[start:start+count].T;delta=x[gj]-x[gi];distance=np.linalg.norm(delta,axis=1)
     correction=delta*((distance-length[start:start+count])/np.maximum(distance,1e-10)/np.maximum(active[gi].astype(float)+active[gj],1))[:,None]
     x[gi]+=correction*active[gi,None]*(.8 if kind==0 else .2);x[gj]-=correction*active[gj,None]*(.8 if kind==0 else .2)
   anchors=d['anchors']>>16;maximum=(d['anchors']&65535)*d['anchor_scale'];delta=x-x[anchors];distance=np.linalg.norm(delta,axis=1)
   hit=active&(distance>maximum);x[hit]=x[anchors[hit]]+delta[hit]*maximum[hit,None]/distance[hit,None]
   moving=x[ids].copy()
   for c in caps:
    a,b=np.array(c['endpoints_m']);v=b-a;t=np.clip((moving-a)@v/max(v@v,1e-12),0,1);delta=moving-a-t[:,None]*v;distance=np.linalg.norm(delta,axis=1);hit=distance<c['radius_m'];moving[hit]+=delta[hit]/np.maximum(distance[hit,None],1e-10)*(c['radius_m']-distance[hit])[:,None]
   delta=moving-rest[ids];distance=np.linalg.norm(delta,axis=1);x[ids]=rest[ids]+delta*np.minimum(1,travel[ids]/np.maximum(distance,1e-10))[:,None];x[~active]=rest[~active]
  velocity=(x-before)*60*.92
 assert np.isfinite(x).all() and np.array_equal(x[~active],rest[~active]);assert np.max(np.linalg.norm(x-rest,axis=1)-travel)<1e-6
 return x

rows=[];baseline={json.loads(p.read_text())['name']:p for p in dump.glob('*.mesh.json')}
for path in sorted((B/'cloth_final').glob('*.mesh.json')):
 mesh=json.loads(path.read_text());name=mesh['name']
 if mesh['lod']!=0 or not any(name.startswith(n) for n in skirt_names):continue
 stem=path.name.removesuffix('.mesh.json');d=read(B/'cloth_final'/(stem+'.bin'));p=np.array(mesh['positions']);render=lbs(p,np.array(mesh['bones']),np.array(mesh['weights']),skin);mapping=d['render_to_sim'];rest=np.zeros((d['vertex_count'],3));rest[mapping]=render
 oldpath=baseline[name];oldmesh=json.loads(oldpath.read_text());oldstem=oldpath.name.removesuffix('.mesh.json');od=read(dump/(oldstem+'.bin'));op=np.array(oldmesh['positions']);assert np.max(abs(op-p))<2e-6;oldrender=lbs(op,np.array(oldmesh['bones']),np.array(oldmesh['weights']),skin);oldrest=np.zeros((od['vertex_count'],3));oldrest[od['render_to_sim']]=oldrender
 base_z=np.zeros(d['vertex_count']);base_z[mapping]=p[:,2];keep=(d['max_distances']>0)&(base_z<height);old_z=np.zeros(od['vertex_count']);old_z[od['render_to_sim']]=op[:,2];oldkeep=(od['max_distances']>0)&(old_z<height)
 edges=d['constraints'];roots=np.zeros(d['vertex_count'],bool)
 for a,b in edges:
  if keep[a] and d['max_distances'][b]==0:roots[b]=True
  if keep[b] and d['max_distances'][a]==0:roots[a]=True
 
 if roots.any():
  overlap=np.maximum(-clearance(rest[roots],new_pose),0);peak=np.flatnonzero(roots)[int(overlap.argmax())];print('ROOT_PEAK',name,int(peak),'reference',p[np.flatnonzero(mapping==peak)[0]],'posed',rest[peak],'new',overlap.max(),'old',np.maximum(-clearance(rest[roots],old_pose),0).max(),flush=True)
 before_overlap=np.maximum(-clearance(oldrest[oldkeep],old_pose),0);after_overlap=np.maximum(-clearance(rest[keep],new_pose),0);root_overlap=np.maximum(-clearance(rest[roots],new_pose),0) if roots.any() else np.array([0.])
 ox=settle(oldrest,od,old_pose);nx=settle(rest,d,new_pose);final=nx[mapping];np.savez_compressed(B/(name+'_settled_comparison.npz'),before=ox[od['render_to_sim']],after=final,indices=mesh['indices'])
 residual=np.maximum(-clearance(nx[keep],new_pose),0);delta=nx[keep]-rest[keep];old_delta=ox[oldkeep]-oldrest[oldkeep]
 rows.append(dict(mesh=name,baseline_initial_mean_overlap_m=float(before_overlap.mean()),initial_mean_overlap_m=float(after_overlap.mean()),baseline_initial_max_overlap_m=float(before_overlap.max()),initial_max_overlap_m=float(after_overlap.max()),fixed_root_max_overlap_m=float(root_overlap.max()),fixed_root_drift_m=0.,max_settled_residual_m=float(residual.max()),p99_settled_residual_m=float(np.quantile(residual,.99)),baseline_mean_vertical_change_m=float(old_delta[:,2].mean()),mean_vertical_change_m=float(delta[:,2].mean()),baseline_raised_fraction=float((old_delta[:,2]>.01).mean()),raised_fraction=float((delta[:,2]>.01).mean()),travel_clamped=True))
 print('PROXY_MEASURED',rows[-1],flush=True)
limits=dict(fixed_root_overlap_m=.006,maximum_residual_m=.015,p99_residual_m=.005,minimum_mean_pressure_reduction=.2)
for row in rows:
 assert row['fixed_root_max_overlap_m']<=limits['fixed_root_overlap_m']
 assert row['max_settled_residual_m']<=limits['maximum_residual_m']
 assert row['p99_settled_residual_m']<=limits['p99_residual_m']
 assert row['initial_mean_overlap_m']<=row['baseline_initial_mean_overlap_m']*(1-limits['minimum_mean_pressure_reduction'])
 assert row['raised_fraction']<=row['baseline_raised_fraction']
report=dict(proxy_limits=limits,status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256((R/'module'/cfg['id']/'AssetPackages'/(prefix+'.tpac')).read_bytes()).hexdigest(),baseline_version='v0.3.1',rows=rows,scope='Final compiled constraints, actual female UI idle frame, 120 gravity steps at 60Hz/10 grouped constraint iterations plus geodesic anchor limits, fixed roots never projected; a CPU diagnostic, not Bannerlord cloth simulation',game_solver_used=False)
(R/'reports/skirt_collision_validation.json').write_text(json.dumps(report,indent=2));print('SKIRT_COLLISION_COMPARISON',rows)
