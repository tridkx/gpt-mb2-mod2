"""One shared proxy with three independent branches; only trails are mapped."""
import json,sys,subprocess,uuid,hashlib,re
from pathlib import Path
import numpy as np
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);B=R/'build';C=json.loads((R/'tools/model_config.json').read_text());common=W/'tools/cloth_compiler'
sys.path.insert(0,str(common));sys.path.insert(0,str(W/'tools/asset_helpers/pipeline'))
from build_assets import vertex_tangents
from cook_cloth import cook
from cloth_payload import read,decode_positions
from mapping_payload import write,project,reconstruct
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def run(args):
 result=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf8',errors='replace')
 with (B/'cloth_build.log').open('a',encoding='utf8') as log:log.write(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError(result.stdout[-4000:]+result.stderr[-4000:])
source=np.load(B/'fitted_model.npz');rawbones=json.loads((B/'source_bones.json').read_text(encoding='utf8'));rot=np.array(C['source_rotation']);scale=C['unit_scale'];original=np.load(B/'raw_model.npz');zoff=original['p'][:,1].min()*scale
rows=[];branches={};points=[];faces=[];alphas=[];indices=[];weights=[];off=0;fi=0
name='emilie_part_16_hat_trail';p=source[name+'_p'];f=source[name+'_f'];a=source[name+'_alpha'];q,owner=np.unique(np.round(p,6),axis=0,return_inverse=True);ff=owner[f];ff=ff[np.linalg.norm(np.cross(q[ff[:,1]]-q[ff[:,0]],q[ff[:,2]]-q[ff[:,0]]),axis=1)>1e-10];aa=np.zeros(len(q));np.maximum.at(aa,owner,a)
edges=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(q),len(q))),directed=False);largest=np.bincount(labels).argmax();ff=ff[(labels[ff]==largest).all(1)];ids=np.unique(ff);remap=np.full(len(q),-1,int);remap[ids]=np.arange(len(ids));ff=remap[ff];q=q[ids];aa=aa[ids]
points.append(q);faces.append(ff);alphas.append(aa);indices.append(np.tile([13,0,0,0],(len(q),1)));weights.append(np.tile([255,0,0,0],(len(q),1)));branches['hat_trail']=list(range(len(ff)));off=len(q);fi=len(ff)
for side in ['左','右']:
 chain=[b for b in rawbones if b['name'].startswith(side+'D_')];chain.sort(key=lambda b:int(b['name'].split('_')[1]));centers=np.array([b['position'] for b in chain])@rot.T*scale;centers[:,2]-=zoff
 # Extend to the observed upper attachment; original chain ends already reach
 # the attached metal ornaments, which follow this same branch by mapping.
 top=centers[0].copy();top[2]=1.304;centers=np.concatenate([top[None],centers]);cols=3;pp=[]
 for c in centers:
  for x in [-.012,0,.012]:pp.append(c+np.array([x,0,0]))
 pp=np.array(pp);ff=[]
 for row in range(len(centers)-1):
  for col in range(cols-1):
   i=row*cols+col;ff.extend([[i,i+cols,i+1],[i+1,i+cols,i+cols+1]])
 ff=np.array(ff);aa=np.minimum(np.maximum(pp[:,2].max()-pp[:,2]-.025,0)*.4,C['cloth_max_distance_m']['back_ribbons']);aa[:cols*2]=0
 points.append(pp);faces.append(ff+off);alphas.append(aa);indices.append(np.tile([11,0,0,0],(len(pp),1)));weights.append(np.tile([255,0,0,0],(len(pp),1)));branches['back_'+side]=list(range(fi,fi+len(ff)));off+=len(pp);fi+=len(ff)
p=np.concatenate(points);f=np.concatenate(faces);a=np.rint(np.concatenate(alphas)*255).astype('u1');bi=np.concatenate(indices);bw=np.concatenate(weights);n=np.zeros_like(p);tri=p[f];fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);np.add.at(n,f.ravel(),np.repeat(fn,3,axis=0));bad=np.linalg.norm(n,axis=1)<1e-9;n[bad]=[0,1,0];n/=np.linalg.norm(n,axis=1)[:,None];uv=np.zeros((len(p),2));t=vertex_tangents(p,f,uv,n)
geo=B/'emilie_cloth_proxy.mgeo'
with geo.open('wb') as out:
 out.write(np.array([0x4f45474d,len(p),f.size],'<i4').tobytes())
 for v in [p,n,t,uv,uv]:out.write(np.asarray(v,'<f4').tobytes())
 color=np.full((len(p),4),255,'u1');color[:,3]=a
 for v in [color,bi,bw]:out.write(np.asarray(v,'u1').tobytes())
 out.write(f.astype('<u4').tobytes())
proxy=dict(name='emilie_cloth_proxy',part='proxy',geometry=str(geo),material='emilie_m00',flags=[],materialFlags=['no_team_color','no_tattoo'],lod=0,vertices=len(p),triangles=len(f),cloth=True,kind='proxy')
geometry=json.loads((B/'geometry.json').read_text());geometry=[g for g in geometry if g['part']!='proxy'];geometry.append(proxy);(B/'mapped_geometry.json').write_text(json.dumps(geometry,indent=2))
spec=json.loads((B/'spec.json').read_text());spec['output']=str(B/'mapped_base.tpac');spec['meshes'].append(dict(name='emilie_cloth_proxy',bodyPart='',template='mesh',groups=[{k:proxy[k] for k in ['name','geometry','material','flags','materialFlags']}]))
(B/'mapped_spec.json').write_text(json.dumps(spec,indent=2));run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','build',B/'mapped_spec.json']);run(['dotnet',B/'package_patch/PackagePatch.dll',B/'mapped_base.tpac',B/'mapped_uncooked.tpac',B/'mapped_geometry.json'])
for project_name,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch'),('MappedClothPatch','mapped_patch')]:
 run(['dotnet','build',common/(project_name+'.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(B/(folder+'_obj'))+'/', '-o',B/folder])
dump=B/'proxy_input';dump.mkdir(exist_ok=True);run(['dotnet',B/'cloth_probe/NativeClothProbe.dll',B/'mapped_uncooked.tpac','emilie_cloth_proxy','--dump-segments',dump]);files=list(dump.glob('*.mesh.json'));assert len(files)==1;mesh=json.loads(files[0].read_text());assert np.max(abs(np.array(mesh['positions'])-p))<2e-6
payload,plan=cook(mesh,{'unanchored':'error'});cooked=B/'proxy_cooked';cooked.mkdir(exist_ok=True);dest=cooked/(plan['guid']+'.bin');dest.write_bytes(payload);plan['path']=str(dest);(cooked/'manifest.json').write_text(json.dumps([plan],indent=2));run(['dotnet',B/'cloth_patch/ClothPatch.dll',B/'mapped_uncooked.tpac',cooked/'manifest.json',B/'proxy_ready.tpac','--allow-metameshes','emilie_cloth_proxy'])
data=read(payload);sim=decode_positions(data);packed=data['rest_normals'];normal=np.column_stack([packed>>21,(packed>>10)&2047,packed&1023])/np.array([2047,2047,1023])*2-1;normal/=np.linalg.norm(normal,axis=1)[:,None];simtris=data['render_to_sim'][f]
renderdump=B/'mapped_render_input';renderdump.mkdir(exist_ok=True);run(['dotnet',B/'cloth_probe/NativeClothProbe.dll',B/'mapped_uncooked.tpac','emilie_body','--dump-segments',renderdump]);maps=B/'render_maps';maps.mkdir(exist_ok=True);manifest=[];reports=[]
for path in sorted(renderdump.glob('*.mesh.json')):
 render=json.loads(path.read_text());rp=np.array(render['positions']);active=np.array(render['alpha'])>0;kind='hat_trail' if 'hat_trail' in render['name'] else 'back_ribbons';mi=np.zeros((len(rp),3),'u2');mw=np.zeros((len(rp),4),'f4');mw[:,0]=1
 selections=[('hat_trail',active)] if kind=='hat_trail' else [('back_左',active&(rp[:,0]<=0)),('back_右',active&(rp[:,0]>0))]
 for branch,sel in selections:
  ids=np.flatnonzero(sel)
  if not len(ids):continue
  ii,ww=project(rp[ids],sim,normal,simtris[np.array(branches[branch])]);mi[ids]=ii;mw[ids]=ww
 error=np.linalg.norm(reconstruct(sim,normal,mi[active],mw[active])-rp[active],axis=1);assert error.max()<.001,(render['name'],error.max())
 blob=write(mi,mw);dest=maps/(render['guid']+'.bin');dest.write_bytes(blob);manifest.append(dict(guid=render['guid'],path=str(dest),sha256=hashlib.sha256(blob).hexdigest(),unmapped_vertices=[]))
 reports.append({'mesh':render['name'],'lod':render['lod'],'kind':kind,'active_vertices':int(active.sum()),'rest_reconstruction_max_error_m':float(error.max()),'max_offset_m':float(abs(mw[active,3]).max())})
(maps/'manifest.json').write_text(json.dumps(manifest,indent=2));native='D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/EmAssetPackages/armor555/armor555.tpac'
run(['dotnet',B/'mapped_patch/MappedClothPatch.dll',B/'proxy_ready.tpac',R/'module/EmilieRace/AssetPackages/emilie.tpac',maps/'manifest.json','emilie_body','emilie_cloth_proxy',native])
(B/'proxy_source.json').write_text(json.dumps(mesh));(B/'proxy_branches.json').write_text(json.dumps(branches));(R/'reports/mapped_cloth.json').write_text(json.dumps({'proxy':plan,'render_maps':reports,'skirt_cloth_enabled':False,'branches':{k:len(v) for k,v in branches.items()},'game_verified':False},indent=2));print('EMILIE_CLOTH_READY',len(reports),'mapped groups')
