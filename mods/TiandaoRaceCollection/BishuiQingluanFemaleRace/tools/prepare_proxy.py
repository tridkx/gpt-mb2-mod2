"""Continuous skirt chart with separate source sleeve, ribbon and fiber islands."""
from pathlib import Path
import json,sys,uuid,re
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
from workspace_paths import workspace_root
from cloth_regions import skirt_mask
from skirt_policy import travel as hem_travel,reference_weights
def prepare(root):
 b=root/'build';cfg=json.loads((root/'tools/model_config.json').read_text());policy=cfg['mapped_cloth'];w=workspace_root(root);sys.path.insert(0,str(w/'tools/asset_helpers/pipeline'));from build_assets import vertex_tangents
 source=np.load(b/'fitted_model.npz');p=source['bql_part_09_p'];sk=source['bql_part_09_sk'];skirt=p[sk];center=np.array(policy['center_xy']);cols,rings=policy['columns'],policy['rings'];theta=np.arange(cols)*2*np.pi/cols;heights=np.linspace(policy['top'],policy['bottom'],rings);rad=skirt[:,:2]-center;angle=np.arctan2(rad[:,1],rad[:,0]);radius=np.linalg.norm(rad,axis=1);radii=[]
 for z in heights:
  row=[]
  for t in theta:
   delta=np.arctan2(np.sin(angle-t),np.cos(angle-t));cost=(delta/.20)**2+((skirt[:,2]-z)/.045)**2;ids=np.argsort(cost)[:10];row.append(float(np.quantile(radius[ids],.1))-.005)
  radii.append(row)
 raw_radii=np.array(radii);radii=np.minimum(raw_radii,gaussian_filter1d(gaussian_filter1d(raw_radii,.7,axis=1,mode='wrap'),.5,axis=0,mode='nearest'))
 positions=np.stack([center[0]+radii*np.cos(theta),center[1]+radii*np.sin(theta),np.repeat(heights[:,None],cols,axis=1)],axis=-1).reshape(-1,3);normals=np.tile(np.column_stack([np.cos(theta),np.sin(theta),np.zeros(cols)]),(rings,1));faces=[]
 for row in range(rings-1):
  for col in range(cols):
   i=row*cols+col;j=row*cols+(col+1)%cols;k=i+cols;l=j+cols;faces.extend([[i,k,j],[j,k,l]])
 faces=np.array(faces);alpha=hem_travel(positions[:,2],policy['hem_policy']);alpha[alpha<.004]=0
 def smooth(a,b,x):
  t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
 dense=reference_weights(positions,policy['hem_policy']);bi=np.argsort(-dense,axis=1)[:,:4];values=np.take_along_axis(dense,bi,axis=1);bw=np.floor(values*255).astype(int);bw[:,0]+=255-bw.sum(1)
 pp=[positions];nn=[normals];aa=[np.rint(alpha*255)];bb=[bi];ww=[bw];ff=[faces];branches=dict(skirt=np.arange(len(faces)).tolist());vo=len(positions);fo=len(faces)
 pins={m['guid']:m['solver_pinned_render_vertices'] for m in json.loads((b/'cooked_cloth/manifest.json').read_text())};lookup={name[:-3]:(cKDTree(source[name[:-3]+'_p']),source[name]) for name in source.files if name.endswith('_sk')}
 for path in sorted((b/'cloth_final').glob('*.mesh.json')):
  m=json.loads(path.read_text())
  if m['lod']!=policy['other_cloth_lod']:continue
  name=re.sub(r'\.lod\d+|\.b\d+','',m['name']);p=np.array(m['positions']);a=np.array(m['alpha']);a[pins[m['guid']]]=0;f=np.array(m['indices']).reshape(-1,3);is_skirt=skirt_mask(name,p,f,source);f=f[(a[f]>0).any(1)&~is_skirt[f].any(1)]
  if not len(f):continue
  area=np.linalg.norm(np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]),axis=1);f=f[area>1e-10];ids=np.unique(f);owner=np.full(len(p),-1);owner[ids]=np.arange(len(ids));pp.append(p[ids]);nn.append(np.array(m['normals'])[ids]);aa.append(a[ids]);bb.append(np.array(m['bones'])[ids]);ww.append(np.array(m['weights'])[ids]);ff.append(owner[f]+vo);branches[name]=np.arange(fo,fo+len(f)).tolist();vo+=len(ids);fo+=len(f)
 mesh=dict(name='bql_cloth_proxy',guid=str(uuid.uuid5(uuid.NAMESPACE_URL,cfg['id']+'/cloth_proxy/mesh')),metamesh='bql_cloth_proxy',lod=0,positions=np.concatenate(pp).tolist(),normals=np.concatenate(nn).tolist(),alpha=np.concatenate(aa).astype(int).tolist(),bones=np.concatenate(bb).tolist(),weights=np.concatenate(ww).tolist(),indices=np.concatenate(ff).ravel().tolist(),skirt_vertices=list(range(len(positions))),chart=dict(center_xy=center.tolist(),top=policy['top'],bottom=policy['bottom'],columns=cols,rings=rings))
 p=np.array(mesh['positions']);n=np.array(mesh['normals']);f=np.array(mesh['indices']).reshape(-1,3);count=len(p);assert count<60000 and f.size<60000
 uv=np.zeros((count,2));t=vertex_tangents(p,f,uv,n);geo=b/'shared_cloth_proxy.mgeo'
 with geo.open('wb') as out:
  out.write(np.array([0x4f45474d,count,f.size],'<i4').tobytes())
  for value in [p,n,t,uv,uv]:out.write(np.asarray(value,'<f4').tobytes())
  colors=np.full((count,4),255,'u1');colors[:,3]=mesh['alpha']
  for value in [colors,mesh['bones'],mesh['weights']]:out.write(np.asarray(value,'u1').tobytes())
  out.write(f.astype('<u4').tobytes())
 (b/'proxy_source.json').write_text(json.dumps(mesh));(b/'proxy_branches.json').write_text(json.dumps(branches));proxy=dict(name=mesh['name'],part='proxy',geometry=str(geo),material='bql_cloth',flags=[],materialFlags=['no_team_color','no_tattoo'],lod=0,vertices=count,triangles=len(f),cloth=True)
 geometry=json.loads((b/'geometry.json').read_text());geometry.append(proxy);(b/'mapped_geometry.json').write_text(json.dumps(geometry,indent=2));spec=json.loads((b/'spec.json').read_text());spec['output']=str(b/'mapped_base.tpac');spec['meshes'].append(dict(name=mesh['metamesh'],bodyPart='',template='mesh',groups=[{k:proxy[k] for k in ['name','geometry','material','flags','materialFlags']}]))
 (b/'mapped_spec.json').write_text(json.dumps(spec,indent=2));(root/'reports/shared_proxy_preparation.json').write_text(json.dumps(dict(status='prepared',proxy_vertices=count,proxy_triangles=len(f),skirt_vertices=len(positions),branches={k:len(v) for k,v in branches.items()},method='Shared skirt chart with source-specific sleeve/ribbon/fiber islands',game_verified=False),indent=2));print('PROXY_READY',count,len(f))
