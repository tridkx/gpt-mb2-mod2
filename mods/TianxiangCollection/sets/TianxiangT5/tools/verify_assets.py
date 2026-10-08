import sys,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/tools'))
sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
MB=r'D:\mb-tools\mbtool\bin\Release\net9.0\mbtool.exe'
PACK=ROOT/'module/TianxiangT5/AssetPackages/tx5.tpac'
out=ROOT/'build/final_export'
rig=parse_skeljson(json.load(open(ROOT/'reports/human_skeleton.json')))
checks={};subs=[]
for file in (out/'geo').glob('*.bin'):subs+=read_geo(file)
assert len(subs)==14, len(subs)
assert all(np.all(s['bw'].sum(1)==255) and s['bi'].max()<=27 for s in subs)
checks['vertices_lod0']=sum(s['nverts'] for s in subs)
checks['triangles_lod0']=sum(s['nidx']//3 for s in subs)
checks['weights_all_sum_255']=True
checks['bone_indices_valid']=True

# Regress the exact reported defect using the final, byte-quantized game asset.
# Skinning any pose must keep the face/body attachment coincident.
arrays=np.load(ROOT/'build/rig_arrays.npz')
body='tx5_body_04';face='tx5_head_11'
source_body=arrays[body+'_S'];source_face=arrays[face+'_S']
ii,jj=np.where(np.linalg.norm(source_body[:,None,:]-source_face[None,:,:],axis=2)<1e-7)
expected=np.unique(arrays[body+'_P'][ii].round(6),axis=0)
assert len(expected)>=18, len(expected)

def attachment(s):
 distance=np.linalg.norm(expected[:,None,:]-s['pos'][None,:,:],axis=2)
 indices=distance.argmin(1)
 assert distance.min(1).max()<2e-6,(s['name'],distance.min(1).max())
 return {k:s[k][indices] for k in ['pos','bi','bw']}

def dense_weights(s):
 w=np.zeros((len(s['pos']),28),int)
 for slot in range(4):w[np.arange(len(w)),s['bi'][:,slot]]+=s['bw'][:,slot]
 return w

seams=[];checks['neck_seams']={}
for lod in range(4):
 lod_subs=subs if lod==0 else [s for f in (ROOT/f'build/final_export_lod{lod}/geo').glob('*.bin') for s in read_geo(f)]
 suffix='' if lod==0 else f'.lod{lod}'
 b=attachment(next(s for s in lod_subs if s['name']==body+suffix))
 h=attachment(next(s for s in lod_subs if s['name']==face+suffix))
 assert np.array_equal(dense_weights(b),dense_weights(h)),f'LOD{lod}: neck weights differ'
 assert np.linalg.norm(b['pos']-h['pos'],axis=1).max()<1e-6
 seams.append((b,h))
 checks['neck_seams'][f'LOD{lod}']={'vertices':len(expected),'weights_identical':True,'rest_gap_mm':float(np.linalg.norm(b['pos']-h['pos'],axis=1).max()*1000),'max_animated_gap_mm':0.0}
for f in (ROOT/'module/TianxiangT5').rglob('*.xml'):ET.parse(f)
checks['xml_valid']=True
checks['animations']={}
for key in ['idle','run','bow','riding']:
 anim=parse_animjson(json.load(open(ROOT/('reports/'+key+'.json'))))
 per=[]
 for frame in np.unique(np.linspace(max(1,anim['start']),anim['frames']-1,12).astype(int)):
  skin=skin_matrices(rig,anim,int(frame))
  for lod,(b,h) in enumerate(seams):
   gap=float(np.linalg.norm(lbs(b['pos'],b['bi'],b['bw'],skin)-lbs(h['pos'],h['bi'],h['bw'],skin),axis=1).max()*1000)
   assert gap<.01,(key,frame,lod,gap)
   check=checks['neck_seams'][f'LOD{lod}'];check['max_animated_gap_mm']=max(check['max_animated_gap_mm'],gap)
  ratios=[];floor=[];worst=[]
  for s in subs:
   p=lbs(s['pos'],s['bi'],s['bw'],skin)
   assert np.isfinite(p).all()
   tri=s['idx'].reshape(-1,3);e=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);rest=np.linalg.norm(s['pos'][e[:,0]]-s['pos'][e[:,1]],axis=1)
   now=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1);valid=rest>.005
   ratio=now[valid]/rest[valid];ratios.extend(ratio.tolist());floor.append(float(p[:,2].min()))
   worst.append((s['name'],float(ratio.max())))
  per.append({'frame':int(frame),'edge_stretch_p99':float(np.percentile(ratios,99)),'edge_stretch_max':float(max(ratios)),'lowest_z':min(floor),'worst_submesh':max(worst,key=lambda w:w[1])})
 checks['animations'][key]=per
for name,cmd in [('metadata',['metacheck',str(PACK)]),('references',['mataudit',str(PACK)])]:
 r=subprocess.run([MB]+cmd,capture_output=True,text=True,encoding='utf-8');checks[name]=r.stdout.strip();assert r.returncode==0,r.stderr
json.dump(checks,open(ROOT/'reports/validation.json','w'),indent=2)
print(json.dumps({k:v for k,v in checks.items() if k!='animations'},ensure_ascii=False,indent=1))
print('ANIMATION_SCAN',[(k,round(max(f['edge_stretch_p99'] for f in v),2),round(max(f['edge_stretch_max'] for f in v),2)) for k,v in checks['animations'].items()])
