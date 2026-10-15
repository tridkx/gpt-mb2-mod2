"""Final TPAC roundtrip, stream correspondence, cloth ownership and native motion."""
import json,sys,subprocess,hashlib,re,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);B=R/'build';C=json.loads((R/'tools/model_config.json').read_text());P=R/'module/EmilieRace/AssetPackages/emilie.tpac';MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();hash_before=sha(P)
sys.path[:0]=[str(W/'tools/asset_helpers/tools'),str(W/'tools/asset_helpers/previewer'),str(W/'tools/cloth_compiler'),str(W/'tools')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
from cloth_payload import read as read_cloth,write as write_cloth
from mapping_payload import read as read_map,write as write_map
from validation import check_structure
from race_action_sets import validate_files
def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,encoding='utf8',errors='replace').stdout
audit=json.loads(run([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',P,'--cloth-vertex-alpha']));assert audit['status']=='pass',audit;(R/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
visible=json.loads(run(['dotnet',W/'tools/AssetTool/AssetTool.dll','visibility',P]));(R/'reports/final_visibility.json').write_text(json.dumps(visible,indent=2));assert all('disable_vertex_color_alpha' in m['ShaderMaterialFlags'] for m in visible['materials'])
geometry=json.loads((B/'geometry.json').read_text());expected_cloth={g['name'] for g in geometry if g.get('cloth')};actual_cloth={m['Name'] for m in visible['meshes'] if 'uses_cloth_simulation' in m['Flags']};assert actual_cloth==expected_cloth
allowed={C['prefix']+f'_part_{i:02d}' for i in C.get('cloth_materials',[])}
assert all(re.sub(r'\.lod\d+$','',name) in allowed for name in expected_cloth)
maps=[];data=None
if C['cloth_enabled']:
 native_roles=json.loads(run(['dotnet',W/'tools/AssetTool/AssetTool.dll','inspect',P,'emilie_body']))[0]
 assert all(m['Flags']==['uses_cloth_simulation'] and not any(m[k] for k in ['UnknownBool1','UnknownBool2','UnknownBool3']) for m in native_roles['meshes'] if 'uses_cloth_simulation' in m['Flags'])
 inspect=B/'mapped_final';run(['dotnet',B/'mapped_patch/MappedClothPatch.dll','--inspect',P,'emilie_body','emilie_cloth_proxy',inspect]);items=json.loads((inspect/'inspection.json').read_text());body=next(m for m in items if m['Name']=='emilie_body');proxy=next(m for m in items if m['Name']=='emilie_cloth_proxy');assert body['ClothMetamesh']==proxy['Guid'];assert body['body']=='emilie_collision' and proxy['body']=='';assert len(proxy['segments'])==1
 direct=proxy['segments'][0];blob=Path(direct['path']).read_bytes();data=read_cloth(blob);check_structure(data);assert write_cloth(data)==blob;plan=json.loads((B/'proxy_cooked/manifest.json').read_text())[0];assert direct['sha256']==plan['sha256'];maps=json.loads((B/'render_maps/manifest.json').read_text());segments={s['OwnerGuid']:s for s in body['segments']};assert len(segments)==len(maps)==len(expected_cloth)
 for row in maps:
  s=segments[row['guid']];assert s['sha256']==row['sha256'];raw=Path(s['path']).read_bytes();i,w=read_map(raw);assert write_map(i,w)==raw and i.max()<data['vertex_count'];assert np.isfinite(w).all() and abs(w[:,:3].sum(1)-1).max()<2e-6
lods=[];exports={}
for lod in range(4):
 folder=B/f'final_export_lod{lod}';run([MB,'exportmod',P,folder,lod]+(['--all-mips'] if lod==0 else []));meshes=[m for path in (folder/'geo').glob('*.bin') for m in read_geo(path) if m['name'].startswith('emilie_part_')];exports[lod]=meshes;rows=[g for g in geometry if g['part']=='body' and g['lod']==lod];assert sum(m['nidx']//3 for m in meshes)==sum(g['triangles'] for g in rows)
 for m in meshes:
  assert m['lod']==lod and np.isfinite(m['pos']).all() and np.isfinite(m['uv']).all();assert m['bi'].max()<28 and (m['bw'].sum(1)==255).all();assert m['idx'].max()<m['nverts'];g=next(g for g in rows if re.sub(r'\.b\d+$','',m['name'])==g['name']);d=Path(g['geometry']).read_bytes();nv=np.frombuffer(d,'<i4',3)[1];p=np.frombuffer(d,'<f4',nv*3,12).reshape(nv,3);uv=np.frombuffer(d,'<f4',nv*2,12+nv*40).reshape(nv,2);bi=np.frombuffer(d,'u1',nv*4,12+nv*60).reshape(nv,4);bw=np.frombuffer(d,'u1',nv*4,12+nv*64).reshape(nv,4)
  # Full position/UV/weight keys resolve coincident UV and normal seams.
  keys=np.column_stack([p,uv,bi,bw]);tree=cKDTree(keys);dist,_=tree.query(np.column_stack([m['pos'],m['uv'],m['bi'],m['bw']]));assert dist.max()<3e-6,(m['name'],dist.max())
 lods.append({'lod':lod,'triangles':sum(m['nidx']//3 for m in meshes),'vertices':sum(m['nverts'] for m in meshes),'submeshes':len(meshes)})
run([MB,'skeljson',P,'emilie_skeleton',R/'reports/final_skeleton.json']);rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));expected=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((B/'skeleton_spec.json').read_text()))]});assert rig['names']==expected['names'] and np.max(abs(rig['restWorld']-expected['restWorld']))<2e-6
pack=json.loads((B/'final_export_lod0/pack.json').read_text());assert {m['name'] for m in pack['meshes']}=={'emilie_body','emilie_hidden'}|({'emilie_cloth_proxy'} if C['cloth_enabled'] else set())
if C['cloth_enabled']:
 proxy_mesh=next(m for m in pack['meshes'] if m['name']=='emilie_cloth_proxy');assert all(m['material']=='emilie_proxy_invisible' for m in proxy_mesh['submeshes'])
 proxy_material=json.loads((R/'reports/material_names.json').read_text())['emilie_proxy_invisible'];assert proxy_material['template']=='alpha' and 'alpha_test' in proxy_material['shaderMaterialFlags'] and proxy_material['alphaTest']>0
sys.path.insert(0,'D:/mb-tools/py');from bcencode import decode_bc1,decode_bc3,decode_bc5
for t in pack['textures']:
 assert t['width']%4==0 and t['height']%4==0,'GPU-incompatible top-level BC texture size'
 blob=(B/'final_export_lod0'/t['file']).read_bytes();assert blob==(B/'tex'/(t['name']+'.bc')).read_bytes();w,h=t['width'],t['height']
 for j,(off,size) in enumerate(zip(t['mipOffset'],t['mipSize'])):
  arr={'DXT1':decode_bc1,'DXT5':decode_bc3,'BC5':decode_bc5}[t['format']](blob[off:off+size],w,h)
  if t['name']=='emilie_proxy_zero':assert arr[:,:,3].max()==0
  if j==0 and t['format']!='BC5':Image.fromarray(arr).save(B/'final_export_lod0/tex'/(t['name']+'.png'))
  w=max(w//2,1);h=max(h//2,1)
motions=[]
for label in ['idle','run','bow','riding','slash','facegen','stand_unarmed','stand_1h','stand_2h']:
 anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()));frames=range(max(1,anim['start']),anim['frames']) if label in ['run','bow','riding','slash'] else sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,64 if label=='facegen' else 16).astype(int)));worst=0;worstframe=1;worstmesh='';p99=0
 # Compute matrices once per frame, then apply every final body group.
 skins={frame:skin_matrices(rig,anim,frame) for frame in frames}
 for m in exports[0]:
  tri=m['idx'].reshape(-1,3);edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);base=np.linalg.norm(m['pos'][edges[:,0]]-m['pos'][edges[:,1]],axis=1);valid=base>.002;edges=edges[valid];base=base[valid]
  for frame,skin in skins.items():
   posed=lbs(m['pos'],m['bi'],m['bw'],skin);assert np.isfinite(posed).all();ratio=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1)/base
   if len(ratio):
    extension=float(ratio.max());p99=max(p99,float(np.quantile(ratio,.99)))
    if extension>worst:worst=extension;worstframe=frame;worstmesh=m['name']
 motions.append({'label':label,'worst_frame':int(worstframe),'worst_mesh':worstmesh,'frames_checked':len(skins),'max_edge_extension':worst,'max_mesh_p99_extension':p99})
 if worst>=6:(R/'reports/motion_failure.json').write_text(json.dumps(motions,indent=2));raise ValueError((label,worstmesh,worst,'gross motion tear'))
actions=validate_files(Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/ModuleData/action_sets.xml'),R/'module/EmilieRace/ModuleData/action_sets.xml','emilie','emilie_skeleton');assert actions['status']=='pass'
for path in (R/'module/EmilieRace').rglob('*.xml'):ET.parse(path)
skins=ET.parse(R/'module/EmilieRace/ModuleData/skins.xml').getroot().find("race[@id='emilie']");assert skins is not None and all(s.get('skeleton')=='emilie_skeleton' and s.get('body_meta_mesh')=='emilie_body' and s.get('hands_mesh')=='emilie_hidden' for s in skins)
runtime=(R/'tools/UIRuntime/Runtime.cs').read_text();assert 'races[data.RaceData]!="emilie"' in runtime and 'MissionScreen' in runtime and 'MapScreen' in runtime;assert 'modern_girl' not in runtime
assert all(sha(R/path)==h for path,h in json.loads((R/'reports/input_hashes.json').read_text(encoding='utf8')).items());assert sha(P)==hash_before;assert json.loads((R/'reports/source_validation.json').read_text())['status']=='pass'
report={'status':'pass','version':C['version'],'date':'2026-10-14','final_package_sha256':hash_before,'source_input_sha256':sha(R/C['source_model']),'baseline_package_sha256':None,'baseline_reason':'First release; preserved selected PMX is the source baseline','game_version':'v1.4.8','check_scope':'Final TPAC geometry, UV, weights, materials, skeleton, mapping/cloth roundtrips, source preservation and native motion scans','lods':lods,'motions':motions,'source_proportions_preserved':True,'cloth_enabled':C['cloth_enabled'],'skirt_cloth_enabled':False,'cloth_render_groups':len(maps),'proxy_simulation_vertices':data['vertex_count'] if data else 0,'metadata_audit':'pass','action_sets_count':actions['registered_count'],'game_test_verified':False,'game_cloth_solver_used':False,'hair_decision':C['hair_decision'],'limitations':['Mapped cloth CPU diagnostics are incomplete; direct proxy diagnostics do not certify render mapping or game physics.','Skirt uses ordinary skinning; riding and deep poses require visual game testing.','Fixed appearance; no facial expressions, face customization or finger grip morphs.','UI/facegen scans are sparse frame samples; run, bow, slash and riding cover full extracted cycles.']}
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
if (R/'reports/motion_failure.json').exists():(R/'reports/motion_failure.json').unlink()
print('RELEASE_VERIFIED',lods,motions)
