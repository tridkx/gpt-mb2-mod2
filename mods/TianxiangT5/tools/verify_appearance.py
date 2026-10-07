"""Validate reread final TPAC, all LODs, original textures and native motions."""
from pathlib import Path
import subprocess,json,hashlib,numpy as np,sys,xml.etree.ElementTree as ET
from appearance_transform import CONFIG,deform
from sleeve_motion import skin_frames,posed
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/no_cloth';DLL=ROOT/'build/sleeve_tool/bin/SleeveTool.dll';MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
def run(args):return subprocess.run([str(x) for x in args],capture_output=True,check=True,text=True,encoding='utf-8').stdout
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for kind in ['baseline','final']:run(['dotnet',DLL,'dump',OUT/('baseline.tpac' if kind=='baseline' else 'tx5.tpac'),OUT/(kind+'.json')])
assert sha(OUT/'baseline.tpac')==CONFIG['baseline_package_sha256']
a={m['name']:m for m in json.loads((OUT/'baseline.json').read_text())};b={m['name']:m for m in json.loads((OUT/'final.json').read_text())};r=json.loads((OUT/'recipe.json').read_text())['meshes'];assert len(a)==len(b)==56
skin='bb703f58-e6a1-1146-e09c-d5058f5affbe';removed=[];head=[]
for name,old in a.items():
 m=b[name];assert not any('cloth' in f for f in m['flags']);assert m['cloth']==old['cloth'] and m['multiplier']==old['multiplier']
 assert m['material']==(skin if name.startswith('tx5_legs_06') else old['material'])
 ids=np.array(r[name]['keep']) if name in r else np.arange(len(old['pos']))
 for key in ['uv','color','bi','bw']:assert np.array_equal(m[key],np.array(old[key])[ids]),(name,key)
 idx=r[name]['idx'] if name in r else old['idx'];assert m['idx']==idx
 p=np.array(m['pos']);n=np.array(m['normal']);t=np.array(m['tangent']);assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(t).all()
 assert np.all(np.array(m['bw']).sum(1)==255) and np.array(m['bi']).min()>=0 and np.array(m['bi']).max()<28
 assert min(idx)>=0 and max(idx)<len(p) and len(idx)%3==0
 if name.startswith('tx5_head_'):
  expected,_=deform(old['pos'],name);assert np.max(np.abs(p-expected))<2e-7
  assert np.max(np.abs(n-np.array(r[name]['normal'])))<.0015
  head.append({'mesh':name,'max_position_error_m':float(np.max(np.abs(p-expected))),'scale':1.2,'neck_transition':name.startswith('tx5_head_11')})
 else:
  assert np.array_equal(p,np.array(old['pos'])[ids]);assert np.array_equal(n,np.array(old['normal'])[ids]);assert np.array_equal(t,np.array(old['tangent'])[ids])
 if name.startswith('tx5_body_00'):removed.append({'mesh':name,'vertices_removed':len(old['pos'])-len(p),'triangles_removed':(len(old['idx'])-len(idx))//3})
assert [x['vertices_removed'] for x in removed]==[300,171,89,46]
seams=[]
for lod in range(4):
 suffix='' if lod==0 else '.lod'+str(lod);aa=b['tx5_body_04'+suffix];bb=b['tx5_head_11'+suffix]
 points=[np.array(m['pos']) for m in [aa,bb]];pairs=[]
 for i,p in enumerate(points[0]):
  hits=np.where(np.linalg.norm(points[1]-p,axis=1)<1e-7)[0]
  for j in hits:
   assert aa['bi'][i]==bb['bi'][j] and aa['bw'][i]==bb['bw'][j]
   assert np.linalg.norm(np.array(aa['normal'][i])-bb['normal'][j])<.0003
   pairs.append((i,int(j)))
 assert len(set(map(tuple,np.round(points[0][[i for i,j in pairs]],6))))==18
 seams.append({'lod':lod,'shared_points':18,'pairs':pairs})
for kind,package in [('baseline',OUT/'baseline.tpac'),('final',OUT/'tx5.tpac')]:
 run([MB,'exportmod',package,OUT/(kind+'_export'),0,'--all-mips'])
basepack=json.loads((OUT/'baseline_export/pack.json').read_text());pack=json.loads((OUT/'final_export/pack.json').read_text());assert basepack['materials']==pack['materials']
mat=next(x for x in pack['materials'] if x['name']=='tx5_skin');assert mat['textures']['0']=='tx5_skin_d' and mat['blendMode']=='no_alpha_blend' and mat['alphaTest']==0
texhash={}
for tex in (OUT/'baseline_export/tex').glob('*.bin'):
 assert tex.read_bytes()==(OUT/'final_export/tex'/tex.name).read_bytes();texhash[tex.name]=sha(tex)
assert len(texhash)==11
for lod in [1,2,3]:run([MB,'exportmod',OUT/'tx5.tpac',OUT/('lod'+str(lod)),lod])
segments=[]
for owner in ['tx5_body','tx5_head','tx5_legs']:
 folder=OUT/'metadata'/owner;run(['dotnet',DLL,'inspect',OUT/'tx5.tpac',owner,folder]);meta=json.loads((folder/'metadata.json').read_text());assert meta['ClothMetamesh']=='00000000-0000-0000-0000-000000000000'
 assert not any(x['type'].startswith(('b97','af416')) for x in meta['segments'])
 for command in ['segcheck','metacheck']:
  result=run([MB,command,OUT/'tx5.tpac',owner]);assert not any(x in result.lower() for x in ['differs','failed','first diff']),result;segments.append(result)
(OUT/'segment_checks.txt').write_text('\n'.join(segments))
audit=json.loads(run([sys.executable,'C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',OUT/'tx5.tpac','--cloth-vertex-alpha']));assert audit['status']=='pass';(ROOT/'reports/appearance_asset_audit.json').write_text(json.dumps(audit,indent=2))
source=json.loads((ROOT/'reports/appearance_source_validation.json').read_text());assert source['status']=='pass'
rig=json.loads((ROOT/'reports/human_skeleton.json').read_text());motions=[]
for label in ['idle','run','bow','riding','grip_twohanded_block','grip_twohanded_thrust']:
 anim=json.loads((ROOT/f'reports/{label}.json').read_text());skins,worlds=skin_frames(rig,anim);error=0
 for skinframe in skins:
  for m in b.values():assert np.isfinite(posed(m,skinframe)).all()
  for seam in seams:
   suffix='' if seam['lod']==0 else '.lod'+str(seam['lod']);ap=posed(b['tx5_body_04'+suffix],skinframe);bp=posed(b['tx5_head_11'+suffix],skinframe)
   error=max(error,max(np.linalg.norm(ap[i]-bp[j]) for i,j in seam['pairs']))
 assert error<1e-7
 frame=0 if label=='idle' else int(np.argmax(np.abs(worlds[:,3,1,3]-worlds[:,7,1,3]))) if label=='run' else len(skins)//2
 np.savez_compressed(OUT/f'review_{label}.npz',**{name:posed(m,skins[frame]) for name,m in b.items() if m['lod']==0})
 motions.append({'animation':anim['name'],'frames':len(skins),'all_lods_finite':True,'max_neck_gap_m':float(error),'preview_frame':frame+1})
for xml in (ROOT/'module/TianxiangT5').rglob('*.xml'):ET.parse(xml)
report={'version':CONFIG['version'],'status':'pass','baseline_version':'v1.4.0','baseline_package_sha256':sha(OUT/'baseline.tpac'),'final_package_sha256':sha(OUT/'tx5.tpac'),'cloth_enabled':False,'all_56_meshes_skinning_only':True,'sleeves_removed':removed,'thigh_material':mat,'head_scale_checks':head,'neck_seams':[{'lod':s['lod'],'shared_points':18} for s in seams],'materials_and_11_textures_unchanged':True,'texture_sha256':texhash,'source_validation':'pass','native_animation_checks':motions,'game_test_verified':False,'limitations':'Offline resource, proportions, seam and skinning checks only. Enlarged hair/accessories and ordinary skirt deformation require game review.'}
(ROOT/'reports/appearance_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['version','status','sleeves_removed','final_package_sha256']},indent=2))
