"""Fit leg capsules to this model and cook the skirt's own LOD0/1 topology."""
import json,sys,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.cluster.vq import kmeans2
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);B=R/'build';C=W/'tools/cloth_compiler'
cfg=json.loads((R/'tools/model_config.json').read_text());j=np.array(cfg['landmarks_m'])
names=[b['name'] for b in json.loads((R/'reports/human_skeleton.json').read_text())['bones']]
source=np.load(B/'fitted_model.npz')
def triangle_samples(p,f):
    tri=p[f];points=[p,tri.mean(1)]
    for i in range(5):
        for j in range(5-i):
            bary=np.array([i,j,4-i-j])/4;points.append((tri*bary[None,:,None]).sum(1))
    return np.concatenate(points)
# Include triangle interiors, so radius fitting is not based only on vertices.
samples=[]
for name in cfg['collision_parts']:
    p=source[name+'_p'];samples.append(triangle_samples(p,source[name+'_f']))
surface=np.concatenate(samples);caps=[]
def add(name,a,b,points,ba,bb):
    # Fit centre as well as radius. A fixed off-centre axis inflated the whole
    # thigh to accommodate crotch samples, pushing the standing skirt outward.
    original_a=a.copy();original_b=b.copy()
    def distance(x):
        aa=a.copy();bb=b.copy();aa[:2]=x[:2];bb[:2]=x[2:]
        axis=bb-aa;t=np.clip((points-aa)@axis/(axis@axis),0,1)
        return np.linalg.norm(points-aa-t[:,None]*axis,axis=1)
    initial=np.r_[a[:2],b[:2]]
    fit=minimize(lambda x:distance(x).max(),initial,method='Powell',
                 bounds=[(v-.025,v+.025) for v in initial],
                 options={'xtol':1e-9,'ftol':1e-9,'maxiter':1000})
    chosen=fit.x if distance(fit.x).max()<distance(initial).max() else initial
    a=a.copy();b=b.copy();a[:2]=chosen[:2];b[:2]=chosen[2:]
    clearance=cfg['collision_clearance_m']
    radius=float(distance(chosen).max()+clearance)
    assert .02<radius<.13,(name,radius)
    caps.append(dict(name=name,endpoints_m=[a.tolist(),b.tolist()],radius_m=radius,bones=[ba,bb],sample_count=len(points),clearance_m=clearance,
                     maximum_sample_exposure_m=float(np.maximum(distance(chosen)-radius,0).max()),
                     initial_endpoints_m=[original_a.tolist(),original_b.tolist()],initial_radius_m=float(distance(initial).max()+.003)))
for prefix,sign,hip,knee,ankle in [('l',-1,1,2,3),('r',1,5,6,7)]:
    side=surface[(surface[:,0]*sign>0)&(surface[:,2]>j[ankle,2])&(surface[:,2]<cfg['shorts_height_band_m'][1])]
    # Stop below the fitted waist: treating the entire pelvis as a round thigh
    # capsule would force the closely fitted skirt root outward.
    top=j[hip].copy();top[2]-=.045
    mid=(j[hip]+j[knee])/2;mid[2]-=.03
    bottom=j[ankle].copy()
    # The shorts/hip end follows the pelvis, so raising a thigh cannot push the
    # enlarged upper cap into the fixed waist seam.
    for label,start,end,ba,bb in [('upper_thigh',top,mid,'pelvis',prefix+'_thigh'),('lower_thigh',mid+[0,0,.045],j[knee],prefix+'_thigh',prefix+'_calf'),('calf',j[knee],bottom,prefix+'_calf',prefix+'_calf')]:
        mask=(side[:,2]>=end[2])&(side[:,2]<=start[2]);points=side[mask];assert len(points)>10
        add(prefix+'_'+label,start,end,points,ba,bb)
# Cover residual upper-shorts patches locally rather than inflating whole legs.
p=source[cfg['shorts_part']+'_p'];tri=p[source[cfg['shorts_part']+'_f']]
shorts=triangle_samples(p,source[cfg['shorts_part']+'_f'])
shorts=shorts[(shorts[:,2]>cfg['shorts_height_band_m'][0])&(shorts[:,2]<cfg['shorts_height_band_m'][1])]
outside=np.full(len(shorts),1e9)
for cap in caps:
    a,b=np.array(cap['endpoints_m']);v=b-a;t=np.clip((shorts-a)@v/(v@v),0,1)
    outside=np.minimum(outside,np.linalg.norm(shorts-a-t[:,None]*v,axis=1)-cap['radius_m'])
missing=np.unique(shorts[outside>0],axis=0)
if len(missing):
    _,groups=kmeans2(missing,min(max(8,int(np.ceil(len(missing)/24))),24,len(missing)),minit='++',seed=202)
    for group in sorted(set(groups)):
        patch=missing[groups==group];center=patch.mean(0)
        center[:2]*=.85;center[2]-=.012
        a=center+[-.003,0,0];b=center+[.003,0,0];v=b-a;t=np.clip((patch-a)@v/(v@v),0,1)
        radius=float(np.linalg.norm(patch-a-t[:,None]*v,axis=1).max()+cfg['collision_clearance_m'])
        endpoint_weights={'pelvis':1.0}
        caps.append(dict(name='shorts_patch_'+str(group).zfill(2),endpoints_m=[a.tolist(),b.tolist()],radius_m=radius,
                         bones=['pelvis','pelvis'],endpoint_weights=[endpoint_weights,endpoint_weights],sample_count=len(patch),clearance_m=.001,maximum_sample_exposure_m=0.0))
root=ET.Element('bodies');body=ET.SubElement(root,'body',name='txgirl2_leg_collision',owner_skeleton=cfg['skeleton']);container=ET.SubElement(body,'capsules')
for cap in caps:
    a,b=np.array(cap['endpoints_m']);axis=b-a;length=np.linalg.norm(axis);u=axis/length;v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);t=np.cross(v,u)
    frame=np.eye(4);frame[:3,:3]=[u,t,v];frame[3,:3]=a
    capsule=ET.SubElement(container,'capsule',name='txgirl2_'+cap['name'],length=f'{length:.6f}',origin='0, 0, 0',frame=', '.join(f'{x:.6f}' for x in frame.ravel()))
    points=ET.SubElement(capsule,'points')
    for weights in cap.get('endpoint_weights',[{bone:1.0} for bone in cap['bones']]):
        point=ET.SubElement(points,'point',radius=f"{cap['radius_m']:.6f}");bones=ET.SubElement(point,'bones')
        for bone,weight in weights.items():ET.SubElement(bones,'bone',name=bone,weight=f'{weight:.8f}')
ET.indent(root,space='  ');ET.ElementTree(root).write(R/'module/TianxiangGirlT2Race/ModuleData/cloth_bodies.xml',encoding='utf-8',xml_declaration=True)
(R/'reports/cloth_collision.json').write_text(json.dumps(dict(capsules=caps,body='txgirl2_leg_collision',engine_verified=False),indent=2))
def run(args):subprocess.run([str(x) for x in args],check=True)
for project,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch')]:
    run(['dotnet','build',C/(project+'.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(B/'cloth_obj'/project)+'/','-o',B/folder])
inputs=B/'cloth_inputs';inputs.mkdir(exist_ok=True)
result=subprocess.run(['dotnet',str(B/'cloth_probe/NativeClothProbe.dll'),str(B/'uncooked.tpac'),'txgirl2_body','--dump-segments',str(inputs)],check=True,capture_output=True,text=True)
(R/'reports/cloth_uncooked.json').write_text(result.stdout)
meshes=[json.loads(p.read_text()) for p in inputs.glob('*.mesh.json')]
assert len(meshes)==2 and {m['lod'] for m in meshes}=={0,1}
policy={'default':{'unanchored':'error'},'meshes':{}}
for mesh in meshes:
    policy['meshes'][mesh['name']]={'unanchored':'pin_upper','axis':2,'band_m':cfg['cloth_root_band_m'],'min_vertices':2,'reason':'T2 source panels attach at separate upper edges; restore only their own top attachment if LOD reduction removes fixed vertices'}
(R/'tools/cloth_policy.json').write_text(json.dumps(policy,indent=2))
run([sys.executable,C/'cook_cloth.py',inputs,B/'cooked_cloth','--policy',R/'tools/cloth_policy.json'])
# Source panel attachments sit within the hip shell. Keep all zero-distance
# roots outside the shader's integration/constraint/capsule movement range.
# Native gpucloth_solver.rs uses simulation_start as the immovable cutoff.
sys.path.insert(0,str(W/'tools'))
from cloth_compiler.cloth_payload import read,write
from cloth_compiler.cook_cloth import batches
import hashlib
manifest_path=B/'cooked_cloth/manifest.json'
cooked=json.loads(manifest_path.read_text())
for entry in cooked:
    payload_path=Path(entry['path'])
    payload=read(payload_path)
    payload['simulation_start']=payload['normal_start']
    # Virtual collision particles write every triangle vertex without checking
    # inverse mass. Exclude triangles touching fixed roots from that path.
    triangles=payload['dummy_indices'].reshape(-1,3)
    triangles=triangles[(triangles>=payload['simulation_start']).all(1)]
    groups=batches(triangles.tolist(),payload['simulation_start'])
    ordered=[];sets=[]
    for group in groups:sets.append([len(group),len(ordered)]);ordered.extend(group)
    payload['dummy_indices']=np.asarray(ordered,'<u4').ravel()
    payload['dummy_sets']=np.asarray(sets,'<i4').reshape(-1,2)
    payload['dummy_index_count']=len(payload['dummy_indices'])
    raw=write(payload);payload_path.write_bytes(raw)
    entry['sha256']=hashlib.sha256(raw).hexdigest()
    entry['bytes']=len(raw);entry['dummy_sets']=len(sets)
    entry['immutable_roots']=True
    entry['simulation_start']=payload['simulation_start']
manifest_path.write_text(json.dumps(cooked,indent=2))
run(['dotnet',B/'cloth_patch/ClothPatch.dll',B/'uncooked.tpac',B/'cooked_cloth/manifest.json',R/'module/TianxiangGirlT2Race/AssetPackages/txgirl2.tpac','--allow-metameshes','txgirl2_body'])
print('CLOTH_READY',len(meshes),'skirts;',len(caps),'leg capsules')
