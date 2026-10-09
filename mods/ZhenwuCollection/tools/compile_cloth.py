"""Compile direct cloth for authorized sets 5-8 and verify final payloads."""
from pathlib import Path
import json,hashlib,subprocess,sys,shutil
from collections import Counter
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[1]
SHARED=next(p for p in [WORKSPACE/'tools/cloth_compiler',ROOT/'workspace_tools/cloth_compiler'] if p.is_dir());sys.path.insert(0,str(SHARED.parent))
from cloth_compiler.cloth_payload import read,write,decode_positions
from cloth_compiler.validation import check_structure
from cloth_input_adapter import adapt_mesh
PROBE=ROOT/'build/cloth_NativeClothProbe/NativeClothProbe.dll';PATCH=ROOT/'build/cloth_ClothPatch/ClothPatch.dll'
SETS=['05_FuyuChongyun','06_XuanjiKongmeng','07_YimoCangming','08_ShenjiTaolue']
TYPE='b97e0f10-df49-4666-8f1d-ada6630d4b4e';EDITOR='3d41985f-24d2-4fc1-82e4-6a6e0da3f4e2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def call(args):return subprocess.check_output(args,encoding='utf8',errors='replace')
def compile_set(setname):
 folder=ROOT/'sets'/setname;cfg=json.loads((folder/'tools/model_config.json').read_text(encoding='utf8'));assert cfg['cooked_cloth']
 package=folder/'module/ZhenwuCollection/AssetPackages'/(cfg['prefix']+'.tpac');basehash=sha(package);base=folder/'build/cloth'/basehash[:16];base.mkdir(parents=True,exist_ok=True)
 original=base/'uncompiled.tpac';shutil.copy2(package,original);inputs=base/'inputs';cooked=base/'cooked';final=base/'final';names=[cfg['prefix']+'_'+s for s in ['head','body','legs']]
 def probe(path,dump):return json.loads(call(['dotnet',str(PROBE),str(path),*names,'--dump-segments',str(dump)]))
 before=probe(original,inputs)
 geometry=json.loads((folder/'build/geometry.json').read_text());policy={'default':{'unanchored':'error'},'meshes':{}}
 for g in geometry:
  if not g['cloth']:continue
  policy['meshes'][g['name']]={'unanchored':'pin_upper','axis':2,'band_m':.012 if g['kind']=='long_hair' else .015,'min_vertices':2,'reason':'Measured upper attachment of '+g['kind']+' component in '+setname+'; existing source fixed vertices retained. Solver-only extra roots recorded per component and per LOD.'}
 (folder/'tools/cloth_policy.json').write_text(json.dumps(policy,indent=2))
 solver_inputs=base/'solver_inputs';solver_inputs.mkdir(exist_ok=True);adapters={}
 for path in inputs.glob('*.mesh.json'):
  adapted,notes=adapt_mesh(json.loads(path.read_text()));adapters[adapted['name']]=notes;(solver_inputs/path.name).write_text(json.dumps(adapted))
 print('COOKING',setname,flush=True)
 print(call([sys.executable,'-B',str(SHARED/'cook_cloth.py'),str(solver_inputs),str(cooked),'--policy',str(folder/'tools/cloth_policy.json')]),flush=True)
 new=base/'compiled.tpac';print(call(['dotnet',str(PATCH),str(original),str(cooked/'manifest.json'),str(new),'--allow-metameshes',*names]),flush=True)
 after=probe(new,final);plans=json.loads((cooked/'manifest.json').read_text());changes={p['guid']:p for p in plans};expected={g['name'] for g in geometry if g['cloth']}
 assert {p['mesh'] for p in plans}==expected
 for mm in after:
  old=next(m for m in before if m['Guid']==mm['Guid'])
  assert {k:v for k,v in mm.items() if k not in ['meshes','segments']}=={k:v for k,v in old.items() if k not in ['meshes','segments']}
  for m in mm['meshes']:
   prior=next(x for x in old['meshes'] if x['Guid']==m['Guid'])
   assert {k:v for k,v in m.items() if k!='edit_bones'}=={k:v for k,v in prior.items() if k!='edit_bones'},(setname,m['Name'],'unrelated runtime change')
   if m['Guid'] in changes:assert m['edit_bones']==m['edit_positions']
   else:assert m==prior
  for seg in old['segments']:
   now=next(s for s in mm['segments'] if s['TypeGuid']==seg['TypeGuid'] and s['OwnerGuid']==seg['OwnerGuid'])
   if seg['TypeGuid']==EDITOR and seg['OwnerGuid'] in changes:continue
   assert now==seg
  assert len(mm['segments'])-len(old['segments'])==sum(p['metamesh']==mm['Name'] for p in plans)
 rows=[]
 for plan in plans:
  path=final/(plan['metamesh']+'_'+plan['guid']+'.bin');raw=path.read_bytes();assert sha(path)==plan['sha256'];data=read(raw);assert write(data)==raw;check_structure(data)
  mesh=json.loads((final/(plan['metamesh']+'_'+plan['guid']+'.mesh.json')).read_text());mesh,adapter=adapt_mesh(mesh);assert adapter==adapters[mesh['name']];mapping=data['render_to_sim'];nv=data['vertex_count'];p=np.asarray(mesh['positions']);pos=np.zeros((nv,3));pos[mapping]=p
  err=float(np.max(np.linalg.norm(decode_positions(data)[mapping]-p,axis=1)));assert err<.00018
  c=data['constraints'];assert np.max(abs(np.linalg.norm(pos[c[:,0]]-pos[c[:,1]],axis=1)-data['rest_lengths']))<2e-7
  alpha=np.asarray(mesh['alpha'],np.float32)/255;alpha[plan['solver_pinned_render_vertices']]=0;assert np.max(abs(data['max_distances'][mapping]-alpha))<1e-6
  assert np.array_equal(data['bone_indices'].reshape(-1,4)[mapping],mesh['bones'])
  assert np.max(abs(data['bone_weights'].reshape(-1,4)[mapping]-np.asarray(mesh['weights'])/255))<1e-7
  assert np.max(abs(data['bone_weights'].reshape(-1,4).sum(1)-1))<1e-6
  tri=mapping[np.asarray(mesh['indices']).reshape(-1,3)];selected=tri[np.any(data['max_distances'][tri]>0,axis=1)]
  assert Counter(map(tuple,selected))==Counter(map(tuple,data['dummy_indices'].reshape(-1,3)))
  e=np.vstack((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]));graph=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(nv,nv)).tocsr();_,labels=connected_components(graph,directed=False)
  assert np.all(labels==labels[data['anchors']>>16]) and np.all(labels[c[:,0]]==labels[c[:,1]])
  row=dict(plan);row.pop('path');row['max_position_compression_error_m']=err;rows.append(row)
 assert {p['lod'] for p in plans}=={0,1}
 # Preserve all material bytes, runtime geometry/skin/UV/Alpha and non-cloth LODs.
 asset=WORKSPACE/'tools/AssetTool/AssetTool.dll'
 old_materials=json.loads(call(['dotnet',str(asset),'visibility',str(original)]))['materials']
 new_materials=json.loads(call(['dotnet',str(asset),'visibility',str(new)]))['materials'];assert old_materials==new_materials
 shutil.copy2(new,package);assert sha(package)==sha(new)
 report={'status':'pass','final_package_sha256':sha(package),'baseline_package_sha256':basehash,'cooked_meshes':rows,'solver_topology_adapters':adapters,'enabled_lods':[0,1],'all_runtime_geometry_alpha_uv_and_skin_preserved':True,'all_materials_unchanged':True,'noncloth_lods_unchanged':True,'editor_skin_completed':True,'explicit_solver_root_overrides_recorded':True,'game_solver_verified':False,'scope':'Native-type direct triangle-network preprocessing, final blob byte identity, constraints, groups, compression, mapping and skin validated; no proxy mapping or engine physics test.'}
 (folder/'reports/cooked_cloth_validation.json').write_text(json.dumps(report,indent=2));print('COOKED_CLOTH_PASS',setname,len(rows),'meshes',flush=True)
def ensure_compiler():
 fingerprint=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(SHARED.glob('*')) if p.is_file())).hexdigest()
 marker=ROOT/'build/cloth_compiler_fingerprint.txt'
 if PROBE.exists() and PATCH.exists() and marker.exists() and marker.read_text()==fingerprint:return
 for name in ['NativeClothProbe','ClothPatch']:
  print(call(['dotnet','build',str(SHARED/(name+'.csproj')),'-o',str(ROOT/'build'/('cloth_'+name)),'-p:BaseIntermediateOutputPath='+str(ROOT/'build'/('cloth_obj_'+name))+'/']),flush=True)
 marker.write_text(fingerprint)
if __name__=='__main__':
 ensure_compiler()
 for setname in (sys.argv[1:] or SETS):
  assert setname in SETS;compile_set(setname)
