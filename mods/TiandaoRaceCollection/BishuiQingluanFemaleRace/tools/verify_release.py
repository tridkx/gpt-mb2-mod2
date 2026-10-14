"""Verify final TPAC, this model's geometry, skinning, registrations and motions."""
import json,sys,subprocess,hashlib,re,xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
from PIL import Image
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);cfg=json.loads((R/'tools/model_config.json').read_text());M=R/'module'/cfg['id'];P=M/'AssetPackages/bql.tpac';MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe';N=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native')
sys.path[:0]=[str(W/'tools/asset_helpers/tools'),str(W/'tools/asset_helpers/previewer'),'D:/mb-tools/py',str(W/'tools')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
from bcencode import decode_bc1,decode_bc3,decode_bc5
from race_action_sets import validate_files
def run(args):return subprocess.check_output([str(x) for x in args],text=True,encoding='utf-8',errors='replace')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original_hash=sha(P);audit=json.loads(run([sys.executable,'-B','-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',P,'--cloth-vertex-alpha']));assert audit['status']=='pass',audit;(R/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
visibility=json.loads(run(['dotnet',W/'tools/AssetTool/AssetTool.dll','visibility',P]));(R/'reports/final_visibility.json').write_text(json.dumps(visibility,indent=2));assert all('disable_vertex_color_alpha' in m['ShaderMaterialFlags'] for m in visibility['materials'])
geometry=json.loads((R/'build/geometry.json').read_text());arrays=np.load(R/'build/fitted_model.npz');lods=[];exports={};source_errors=[]
for lod in range(4):
 folder=R/'build'/f'final_export_lod{lod}';run([MB,'exportmod',P,folder,lod]+(['--all-mips'] if lod==0 else []));meshes=[m for p in (folder/'geo').glob('*.bin') for m in read_geo(p) if not m['name'].startswith(('bql_hidden','bql_cloth_proxy'))];assert len(meshes)==16
 for m in meshes:
  assert np.isfinite(m['pos']).all() and np.isfinite(m['uv']).all();assert m['bi'].max()<28 and (m['bw'].sum(1)==255).all();assert m['idx'].max()<m['nverts'];assert m['lod']==lod
  if lod==0:
   name=re.sub(r'\.b\d+$','',m['name']);dist,_=cKDTree(arrays[name+'_p']).query(m['pos']);assert dist.max()<2e-6;source_errors.append(float(dist.max()))
 for hand in [19,26]:assert sum(int(((m['bi']==hand)&(m['bw']>0)).sum()) for m in meshes)>50
 expected=sum(g['triangles'] for g in geometry if g['part']=='body' and g['lod']==lod);assert sum(m['nidx']//3 for m in meshes)==expected
 exports[lod]=meshes;lods.append(dict(lod=lod,triangles=expected,vertices=sum(m['nverts'] for m in meshes)))
assert all(lods[i+1]['triangles']<lods[i]['triangles'] for i in range(3))
folder=R/'build/final_export_lod0';pack=json.loads((folder/'pack.json').read_text());assert {m['name'] for m in pack['meshes']}=={'bql_body','bql_hidden','bql_cloth_proxy'}
textures=[]
for t in pack['textures']:
 blob=(folder/t['file']).read_bytes();assert blob==(R/'build/tex'/(t['name']+'.bc')).read_bytes();assert t['mipsExported']==t['mipCount'];w,h=t['width'],t['height']
 for i,(offset,size) in enumerate(zip(t['mipOffset'],t['mipSize'])):
  a={'DXT1':decode_bc1,'DXT5':decode_bc3,'BC5':decode_bc5}[t['format']](blob[offset:offset+size],w,h)
  if t['format']=='BC5':
   rgba=np.full((h,w,4),255,'u1');rgba[:,:,:2]=a;xy=a.astype(float)/127.5-1;rgba[:,:,2]=np.round((np.sqrt(np.maximum(1-(xy*xy).sum(2),0))+1)*127.5).astype('u1');a=rgba
  assert a.shape==(h,w,4)
  if i==0:Image.fromarray(a).save(folder/'tex'/(t['name']+'.png'))
  w=max(1,w//2);h=max(1,h//2)
 textures.append(dict(name=t['name'],all_mips_decoded=True))
run([MB,'skeljson',P,cfg['skeleton'],R/'reports/final_skeleton.json']);rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));expected=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((R/'build/skeleton_spec.json').read_text()))]});assert rig['names']==expected['names'] and np.abs(rig['restWorld']-expected['restWorld']).max()<2e-6
actions=validate_files(N/'ModuleData/action_sets.xml',M/'ModuleData/action_sets.xml',cfg['race'],cfg['skeleton'],legacy_prefix='bql');skins=ET.parse(M/'ModuleData/skins.xml').find(f"race[@id='{cfg['race']}']");assert len(skins)==len(ET.parse(N/'ModuleData/skins.xml').find("race[@id='human']"))
for skin in skins:assert skin.get('skeleton')==cfg['skeleton'] and skin.get('body_meta_mesh')=='bql_body' and skin.get('hands_mesh')=='bql_hidden'
troops=ET.parse(M/'ModuleData/test_troop.xml').getroot();assert len(troops)==1 and troops[0].get('id')=='bql_test' and troops[0].get('race')==cfg['race'] and troops[0].get('is_female')=='true';assert not any(e.get('slot') in ['Head','Body','Leg','Gloves','Cape'] for e in troops.findall('.//equipment'))
for path in M.rglob('*.xml'):ET.parse(path)
runtime=R/'tools/UIRuntime/Runtime.cs';rs=runtime.read_text();assert '"'+cfg['race']+'"' in rs and 'bql_default' not in rs and (M/'bin/Win64_Shipping_Client/BishuiQingluanFemaleRace.UIRuntime.dll').is_file()
motions=[]
for label in ['ui_neutral_female','run','bow','riding','slash']:
 anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()));assert anim['have'].all();frames=list(range(max(1,anim['start']),min(anim['frames'],122))) if label=='ui_neutral_female' else list(range(max(1,anim['start']),anim['frames']));matrices={frame:skin_matrices(rig,anim,frame) for frame in frames};worst=0;worst_frame=frames[0];maxp99=0
 for m in exports[0]:
  tri=m['idx'].reshape(-1,3);e=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);base=np.linalg.norm(m['pos'][e[:,0]]-m['pos'][e[:,1]],axis=1);keep=base>.003;e=e[keep];base=base[keep]
  for frame,skin in matrices.items():
   p=lbs(m['pos'],m['bi'],m['bw'],skin);assert np.isfinite(p).all();ratio=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)/base
   if len(ratio):
    r=float(ratio.max());maxp99=max(maxp99,float(np.quantile(ratio,.99)))
    if r>worst:worst=r;worst_frame=frame
 motions.append(dict(label=label,frames_checked=len(frames),worst_frame=worst_frame,max_edge_extension=worst,max_p99_extension=maxp99,cloth_solver_used=False))
assert all(sha(R/p)==h for p,h in json.loads((R/'reports/input_hashes.json').read_text()).items());assert sha(P)==original_hash
report=dict(status='pass',version=cfg['version'],final_package_sha256=original_hash,check_scope='Final TPAC structure, decoded textures, source geometry, weights, native motion and race registrations',lods=lods,textures=textures,motions=motions,source_proportions_preserved=True,source_geometry_max_error_m=max(source_errors),integrated_hands_all_lods=True,registration=dict(status='pass',race=cfg['race'],test_troop='bql_test',native_troop_overrides=False,skin_variants=len(skins),action_sets=actions),game_test_verified=False,game_cloth_solver_used=False,limitations=['Mapped cloth requires user game validation; native motion scan is skinning only.','No facial morphs/expressions; no native recruitment or troop tree replacement.'])
report['visual_acceptance_status']=cfg.get('visual_acceptance_status','pending_game_test')
report['offline_dynamic_risks']=['Body/skirt penetration still needs game retesting; sleeves use ordinary skinning without cloth simulation.']
report['sleeve_simulation_enabled']=cfg.get('sleeve_cloth_enabled',False)
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(status='pass',lods=lods,motions=motions),indent=2))
