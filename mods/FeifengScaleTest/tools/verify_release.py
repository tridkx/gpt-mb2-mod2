import sys,json,hashlib,subprocess,struct
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build';PKG=R/'module/FeifengScaleTest/AssetPackages/ffs.tpac';MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
sys.path[:0]=[str(WS/'tools/asset_helpers/tools'),str(WS/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline= B/'baseline_v0.1.0.tpac'
baseline_hash=sha(baseline) if baseline.exists() else json.loads((R/'reports/visibility_repair.json').read_text())['baseline_sha256']
def run(cmd,path):
 process=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');path.write_text((process.stdout+'\n'+process.stderr).rstrip()+'\n');assert process.returncode==0,(cmd,process.stderr);return process.stdout
run([MB,'metacheck',str(PKG)],R/'reports/metacheck.txt');run([MB,'mataudit',str(PKG)],R/'reports/mataudit.txt')
visibility=json.loads(run(['dotnet',str(WS/'tools/AssetTool/AssetTool.dll'),'visibility',str(PKG)],R/'reports/visibility.json'))
rig=parse_skeljson(json.loads((R/'reports/human_skeleton.json').read_text()));plan=json.loads((R/'reports/scale_plan.json').read_text());native=rig['restWorld'];inv=np.linalg.inv(native)
for lod in range(4):run([MB,'exportmod',str(PKG),str(B/f'final_export{lod}'),str(lod),'--all-mips'],R/'reports'/f'export_lod{lod}.txt')
groups=[g for lod in range(4) for path in (B/f'final_export{lod}/geo').glob('*.bin') for g in read_geo(path)]
assert len(groups)==80,len(groups)
for group in groups:
 assert np.isfinite(group['pos']).all() and np.isfinite(group['uv']).all()
 assert group['bi'].max()<28 and np.all(group['bw'].astype(int).sum(1)==255)
 assert group['idx'].min()>=0 and group['idx'].max()<len(group['pos'])
 assert group['material'] in {'ffs_mat_'+str(i) for i in range(9)}
# Check every mesh against actual exported geometry, including UV and weights.
geometry={row['name'].lower():row for row in json.loads((B/'geometry.json').read_text())}
for group in groups:
 row=geometry[group['name']];data=Path(row['geometry']).read_bytes();_,count,indices=struct.unpack_from('<iii',data);offset=12
 p=np.frombuffer(data,'<f4',count*3,offset).reshape(-1,3);offset+=count*(3+3+4+2+2)*4
 colors=np.frombuffer(data,'u1',count*4,offset);offset+=count*4;bi=np.frombuffer(data,'u1',count*4,offset).reshape(-1,4);offset+=count*4;bw=np.frombuffer(data,'u1',count*4,offset).reshape(-1,4)
 assert np.array_equal(p,group['pos']) and np.array_equal(bi,group['bi']) and np.array_equal(bw,group['bw'])
assert {g['lod'] for g in groups}=={0,1,2,3}
for p in ['A','B']:
 for part in ['head','body','legs']:
  for lod in range(4):assert any(g['name'].startswith(f'ffs_{p.lower()}_{part}_') and g['lod']==lod for g in groups)
ET.parse(R/'module/FeifengScaleTest/SubModule.xml');items=ET.parse(R/'module/FeifengScaleTest/ModuleData/items.xml');assert len(items.findall('Item'))==12
for item in items.findall('Item'):assert item.get('mesh')==item.get('mesh').lower()
for part in ['head','body','legs']:
 for profile in 'CD':
  assert items.find("Item[@id='ffs_%s_%s']"%(profile,part)).get('mesh')=='ffs_a_'+part
assert all(g['name']==g['name'].lower() for g in groups)
original=Path('D:/dsh-tiandao/飞凤苗银(女)');input_hashes={}
for path in (R/'input').iterdir():
 if path.name=='.gitkeep':continue
 assert sha(path)==sha(original/path.name);input_hashes[path.name]=sha(path)
for path in (R/'tex').glob('*.png'):assert sha(path)==sha(original/'tex'/path.name)
motions={};preview={}
animations={name:parse_animjson(json.loads((R/'reports'/f'{name}.json').read_text())) for name in ['run','bow']}
for profile in ['A','B']:
 scales=np.array(plan['profiles'][profile]);selected=[g for g in groups if g['lod']==0 and g['name'].startswith('ffs_'+profile.lower()+'_')]
 def matrices(animation=None,frame=0):
  out=np.zeros_like(native)
  for i in range(28):
   local=rig['restLocal'][i].copy()
   if animation is not None:
    local[:3,:3]=q2R(animation['quat'][i,frame]);
    if rig['parent'][i]<0:local[:3,3]+=animation['rootPos'][frame]
   local[:3,:3]=local[:3,:3]@np.diag(scales[i]);parent=rig['parent'][i];out[i]=local if parent<0 else out[parent]@local
  return out@inv
 rest=matrices();points=np.concatenate([lbs(g['pos'],g['bi'],g['bw'],rest) for g in selected]);assert np.isfinite(points).all()
 preview[profile+'_rest']={g['name']:lbs(g['pos'],g['bi'],g['bw'],rest) for g in selected}
 for name,animation in animations.items():
  assert animation['have'].all() and animation['frames']>=2
  worst=(0,animation['start']);baseline={}
  for g in selected:
   f=g['idx'].reshape(-1,3);p=lbs(g['pos'],g['bi'],g['bw'],rest);baseline[g['name']]=np.maximum(np.linalg.norm(p[f[:,1]]-p[f[:,0]],axis=1),1e-5)
  for frame in range(animation['start'],animation['frames']):
   mats=matrices(animation,frame);score=0
   for g in selected:
    p=lbs(g['pos'],g['bi'],g['bw'],mats);assert np.isfinite(p).all();f=g['idx'].reshape(-1,3);ratio=np.linalg.norm(p[f[:,1]]-p[f[:,0]],axis=1)/baseline[g['name']];score=max(score,float(np.quantile(ratio,.99)))
   if score>worst[0]:worst=(score,frame)
  motions[profile+'_'+name]=dict(animation=animation['name'],frames=animation['frames']-animation['start'],worst_frame=worst[1],edge_ratio_p99=worst[0],finite=True,method='experimental local scale hierarchy; no engine physics or IK')
  mats=matrices(animation,worst[1]);preview[profile+'_'+name]={g['name']:lbs(g['pos'],g['bi'],g['bw'],mats) for g in selected}
np.savez_compressed(B/'preview_positions.npz',**{scene+'__'+name:positions for scene,meshes in preview.items() for name,positions in meshes.items()})
report=dict(status='pass',version='v0.1.2',scope='offline structural checks and experimental predicted skinning only',final_package_sha256=sha(PKG),baseline_sha256=baseline_hash,runtime_dll_sha256=sha(R/'module/FeifengScaleTest/bin/Win64_Shipping_Client/FeifengScaleTest.dll'),source_multiplier=1.5,source_total_height_m=plan['source_total_height_m'],input_hashes=input_hashes,metameshes=6,mesh_groups=80,lods=4,items=12,motions=motions,cloth_enabled=False,game_verified=False,engine_scale_convention_verified=False,inventory_preview_supported=False,appearance_quality_verified=False,known_visual_issues=['sleeve/cuff and shoulder deformation','skirt/panel deformation in predicted motion'],delivery_type='experimental mechanism probe, not production equipment')
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
