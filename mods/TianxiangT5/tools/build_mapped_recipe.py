"""Generate route-2 simulation geometry, cooked fabric and render mappings."""
from pathlib import Path
import json,struct
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import root
from cloth_format import cook,read_cook,write_cook,unpack_positions,write_mapping

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/mapped';OUT.mkdir(exist_ok=True)
config=json.loads((ROOT/'tools/mapped_sleeves_config.json').read_text())
meshes={m['name']:m for m in json.loads((ROOT/'build/sleeve_final.json').read_text())}
mask=np.load(ROOT/'build/sleeve_mask.npz')
sources=[];pos=[];normal=[];faces=[];alpha=[];bones=[];weights=[];regions=[]
selections=[('tx5_body_00',mask['streamers'])]
if config['simulate_skirt']:selections.append(('tx5_body_03',np.ones(len(meshes['tx5_body_03']['pos']),dtype=bool)))
for name,selection in selections:
    m=meshes[name];p=np.array(m['pos']);ids=np.flatnonzero(selection)
    _,reps,inv=np.unique(np.round(p[ids],5),axis=0,return_index=True,return_inverse=True)
    selected=ids[reps];index={int(i):int(j) for i,j in zip(ids,inv)}
    local=np.array([[index[int(i)] for i in tri] for tri in np.array(m['idx']).reshape(-1,3) if all(int(i) in index for i in tri)])
    assert all(len(set(tri))==3 for tri in local)
    offset=len(pos);faces.extend((local+offset).tolist());pos.extend(p[selected].tolist())
    normal.extend(np.array(m['normal'])[selected].tolist())
    bones.extend(np.array(m['bi'])[selected].tolist());weights.extend((np.array(m['bw'])[selected]/255).tolist())
    effective=np.array(m['color'])[selected,3]/255*m['multiplier']
    if name=='tx5_body_03':effective*=config['skirt_distance_scale']
    alpha.extend((effective/2).tolist())
    sources.extend({'mesh':name,'index':int(i)} for i in selected)
    regions.append({'source':name,'vertices':len(selected),'triangles':len(local),'fixed':int((effective==0).sum())})
p=np.array(pos);norm=np.array(normal);f=np.array(faces)
data,reorder,cookedp,cookednormal=cook(p,norm,f,alpha,bones,weights)
(OUT/'proxy_cooked.bin').write_bytes(data)
incident=[[] for _ in p]
for tri in f:
    for i in tri:incident[i].append(tri)
tail_points=len([x for x in sources if x['mesh']=='tx5_body_00'])
trees={'tx5_body_00':(cKDTree(p[:tail_points]),0)}
if config['simulate_skirt']:trees['tx5_body_03']=(cKDTree(p[tail_points:]),tail_points)
mapped={};mapping_reports=[]
mapping_names=['tx5_body_00']+['tx5_body_00.lod'+str(lod) for lod in config['render_lods'] if lod]
if config['simulate_skirt']:mapping_names.append('tx5_body_03')
for name in mapping_names:
    m=meshes[name];points=np.array(m['pos']);source='tx5_body_00' if name.startswith('tx5_body_00') else name
    if source=='tx5_body_00':
        _,nearest=cKDTree(mask['pos']).query(points)
        active=mask['streamers'][nearest]&(mask['alpha'][nearest]>0)
        render_alpha=np.where(active,255,0).tolist()
    else:
        active=np.array(m['color'])[:,3]>0;render_alpha=np.array(m['color'])[:,3].tolist()
    ids=np.tile(reorder[f[0]],(len(points),1));w=np.tile([1.,0.,0.,0.],(len(points),1));errors=[]
    tree,offset=trees[source]
    for i in np.flatnonzero(active):
        distance,j=tree.query(points[i]);j+=offset
        best=None
        for tri in incident[j]:
            q=p[tri];n=norm[tri]
            # Interpolated normal is part of the mapping basis. At coincident
            # vertices this reduces to exact one-hot barycentric coordinates.
            def reconstruct(x):
                b=np.array([x[0],x[1],1-x[0]-x[1]])
                return b@q+x[2]*(b@n)
            initial=np.linalg.lstsq(np.column_stack([q[0]-q[2],q[1]-q[2],n.mean(0)]),points[i]-q[2],rcond=None)[0]
            solution=root(lambda x:reconstruct(x)-points[i],initial)
            x=solution.x;b=np.array([x[0],x[1],1-x[0]-x[1]])
            err=float(np.linalg.norm(reconstruct(x)-points[i]))
            score=err*1000+max(0,-float(b.min()))+abs(float(x[2]))
            if best is None or score<best[0]:best=(score,tri,np.r_[b,x[2]],err)
        assert best is not None and best[3]<2e-6,(name,i,best)
        ids[i]=reorder[best[1]];w[i]=best[2];errors.append(best[3])
    path=OUT/(name+'.mapping.bin');path.write_bytes(write_mapping(ids,w))
    rec=(cookedp[ids]*w[:,:3,None]).sum(1)+(cookednormal[ids]*w[:,:3,None]).sum(1)*w[:,3,None]
    assert np.max(np.linalg.norm(rec[active]-points[active],axis=1))<2e-6
    mapped[name]={'alpha':render_alpha,'file':str(path)}
    mapping_reports.append({'mesh':name,'mapped_vertices':int(active.sum()),'max_reconstruction_error_m':float(max(errors))})

# Independent native samples: verify the entire layout and physical constraints.
native=[]
for folder in ['native_proxy','native_coat']:
    path=ROOT/'build/cloth_format'/folder
    blob=next(path.glob('*b97*.bin')).read_bytes();c=read_cook(blob)
    assert write_cook(c)==blob
    m=json.loads((path/'meshes.json').read_text())[0]
    q=np.zeros((c['header'][2],3));q[c['render_to_particle']]=m['pos']
    error=np.max(np.abs(np.linalg.norm(q[c['pairs'][:,0]]-q[c['pairs'][:,1]],axis=1)-c['lengths']))
    assert error<1e-6
    position_error=np.max(np.linalg.norm(unpack_positions(c['positions'])-q,axis=1));assert position_error<.0002
    native.append({'sample':m['name'],'codec_byte_exact':True,'constraint_max_error_m':float(error),'compressed_position_max_error_m':float(position_error)})
recipe={'proxy_guid':'38b3fcd7-11ad-43e2-aae8-79026a91e86c','proxy_mesh_guid':'431abf07-5dcd-43c8-ae7e-a9b278c426c6',
        'name':'tx5_cloth_simulation','sources':sources,'faces':f.ravel().tolist(),
        'alpha':np.rint(np.array(alpha)*255).astype(int).tolist(),'cooked':str(OUT/'proxy_cooked.bin'),
        'mapped':mapped,'multiplier':2.,'material':config['material'],'flags':config['flags'],
        'disabled_render_meshes':[] if config['simulate_skirt'] else ['tx5_body_03']}
(OUT/'recipe.json').write_text(json.dumps(recipe,indent=2))
report={'version':config['version'],'route':'mapped simulation, offline authored TPAC segments','regions':regions,'mappings':mapping_reports,
        'native_format_checks':native,'cooked_particles':len(p),'cooked_constraints':read_cook(data)['header'][1],
        'skirt_distance_scale':config['skirt_distance_scale'],'material':config['material'],'flags':config['flags'],
        'simulate_skirt':config['simulate_skirt'],
        'note':'Skirt uses accepted skinning only. Proxy and mappings contain sleeves only; no skirt tether or particle can affect sleeve simulation.',
        'official_solver_used':False}
(ROOT/'reports/mapped_sleeves_generation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
