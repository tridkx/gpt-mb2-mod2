"""Check final TPAC re-export, XML, all LODs, byte weights and native motion."""
from pathlib import Path
import json,hashlib,sys,subprocess,struct,re,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[1]
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'));sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
sys.path.insert(0,'D:/mb-tools/py')
from bcencode import decode_bc1,decode_bc3,decode_bc5
def decode_bc(blob,w,h,fmt):
    a={'DXT1':decode_bc1,'DXT5':decode_bc3,'BC5':decode_bc5}[fmt](blob,w,h)
    if fmt=='BC5':
        xy=a.astype(float)/127.5-1;z=np.sqrt(np.maximum(1-(xy*xy).sum(2),0))
        rgba=np.full((h,w,4),255,'u1');rgba[:,:,:2]=a;rgba[:,:,2]=np.round((z+1)*127.5).astype('u1');return rgba
    return a
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe';PACKAGE=ROOT/'module/YueQingShuRace/AssetPackages/yqs.tpac'
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf8',errors='replace').stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
hash_before=sha(PACKAGE)
audit=json.loads(run([sys.executable,'-B','-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(PACKAGE)]));assert audit['status']=='pass',audit
(ROOT/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
visible=json.loads(run(['dotnet',str(WORKSPACE/'tools/AssetTool/AssetTool.dll'),'visibility',str(PACKAGE)]))
(ROOT/'reports/final_visibility.json').write_text(json.dumps(visible,indent=2))
assert all('disable_vertex_color_alpha' in m['ShaderMaterialFlags'] for m in visible['materials'])
assert all(not m['Flags'] and m['AlphaMin']==255 and m['AlphaMax']==255 for m in visible['meshes']), 'Unexpected cloth or vertex transparency'
exports={};lods=[];geometry=json.loads((ROOT/'build/geometry.json').read_text())
def mgeo(path):
    data=Path(path).read_bytes();magic,n,ni=np.frombuffer(data,'<i4',3);assert magic==0x4f45474d
    off=12;p=np.frombuffer(data,'<f4',n*3,off).reshape(n,3);off+=n*12
    normal=np.frombuffer(data,'<f4',n*3,off).reshape(n,3);off+=n*12
    tangent=np.frombuffer(data,'<f4',n*4,off).reshape(n,4);off+=n*16
    uv=np.frombuffer(data,'<f4',n*2,off).reshape(n,2);off+=n*16
    color=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
    bi=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
    bw=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
    idx=np.frombuffer(data,'<u4',ni,off).reshape(-1,3);off+=ni*4;assert off==len(data)
    assert np.isfinite(normal).all() and np.isfinite(tangent).all() and np.isfinite(uv).all()
    assert (np.abs(np.linalg.norm(normal,axis=1)-1)<.03).all()
    return p,uv,bi,bw,idx
def dense(m):
    w=np.zeros((len(m['pos']),28),dtype='u2');np.add.at(w,(np.arange(len(w))[:,None],m['bi']),m['bw']);return w

for lod in range(4):
    folder=ROOT/'build'/f'final_export_lod{lod}';run([MB,'exportmod',str(PACKAGE),str(folder),str(lod)]+(['--all-mips'] if lod==0 else []))
    meshes=[m for p in (folder/'geo').glob('*.bin') for m in read_geo(p) if not m['name'].startswith('yqs_hidden')];exports[lod]=meshes
    assert meshes and all(m['lod']==lod for m in meshes)
    for m in meshes:
        assert np.isfinite(m['pos']).all() and np.isfinite(m['uv']).all()
        assert m['bi'] is not None and m['bi'].max()<28
        assert (m['bw'].sum(1)==255).all()
        assert m['idx'].min()>=0 and m['idx'].max()<m['nverts']
    rows=[g for g in geometry if g['lod']==lod and g['part']!='hidden'];assert sum(m['nidx']//3 for m in meshes)==sum(g['triangles'] for g in rows)
    for g in rows:
        p,uv,bi,bw,idx=mgeo(g['geometry']);expected=dense({'pos':p,'bi':bi,'bw':bw});tree=cKDTree(p)
        matched=[m for m in meshes if re.sub(r'\.b\d+$','',m['name'])==g['name']];assert matched,g['name']
        for m in matched:
            dist,near=tree.query(m['pos']);assert dist.max()<2e-6
            assert np.array_equal(dense(m),expected[near]),m['name']
    lods.append({'lod':lod,'vertices':sum(m['nverts'] for m in meshes),'triangles':sum(m['nidx']//3 for m in meshes),'submeshes':len(meshes)})
assert all(lods[i+1]['triangles']<lods[i]['triangles'] for i in range(3)),lods
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
rigdata=json.loads((ROOT/'reports/human_skeleton.json').read_text())
hand_indices={i for i,b in enumerate(rigdata['bones']) if b['name'] in ['l_hand','r_hand']}
for lod,meshes in exports.items():
    for hand in hand_indices:
        assert sum(int(((m['bi']==hand)&(m['bw']>0)).sum()) for m in meshes)>50,('missing hand influence',lod,hand)

# Verify source points shared across different pieces/materials survived LOD
# reduction with matching quantized influences; exclude free-standing hair.
arrays=np.load(ROOT/'build/fitted_model.npz');manifest=json.loads((ROOT/'build/manifest.json').read_text());cuts={}
for rec in manifest:
    if rec['kind']=='hair':continue
    for i,p in enumerate(arrays[rec['object']+'_p']):cuts.setdefault(tuple(np.round(p,5)),[]).append((rec['object'],i,rec['part']))
cuts={p:r for p,r in cuts.items() if len({n for n,i,part in r})>1};seams=[]
for lod,meshes in exports.items():
    byname={}
    for rec in manifest:
        name=rec['object']+('' if lod==0 else '.lod'+str(lod));rows=[m for m in meshes if re.sub(r'\.b\d+$','',m['name'])==name]
        p=np.concatenate([m['pos'] for m in rows]);w=np.concatenate([dense(m) for m in rows]);byname[rec['object']]=(p,w,cKDTree(p))
    tested=0;cross=0;drift=0
    for refs in cuts.values():
        ref=None
        for name,i,part in refs:
            p,w,tree=byname[name];dist,near=tree.query(arrays[name+'_p'][i]);drift=max(drift,float(dist));assert dist<3e-6,(lod,name,dist)
            if ref is not None:assert np.array_equal(ref,w[near]),(lod,name,'seam weights')
            ref=w[near]
        tested+=1;cross+=int(len({part for name,i,part in refs})>1)
    seams.append({'lod':lod,'shared_points':tested,'cross_equipment_points':cross,'max_position_error':drift})

folder=ROOT/'build/final_export_lod0';pack=json.loads((folder/'pack.json').read_text());texturechecks=[]
assert {m['name'] for m in pack['meshes']} == {'yqs_body','yqs_hidden'}
body=next(m for m in pack['meshes'] if m['name']=='yqs_body')
assert len(body['submeshes'])>=10
assert body['lodAvailable']==[0,1,2,3]
hidden=next(m for m in pack['meshes'] if m['name']=='yqs_hidden')
assert sum(m['triangleCount'] for m in hidden['submeshes'])==4
assert len(pack['skeletons'])==1
run([MB,'skeljson',str(PACKAGE),cfg['skeleton'],str(ROOT/'reports/final_skeleton.json')])
custom=parse_skeljson(json.loads((ROOT/'reports/final_skeleton.json').read_text()))
expected=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((ROOT/'build/skeleton_spec.json').read_text()))]})
assert custom['names']==expected['names'] and np.max(abs(custom['restWorld']-expected['restWorld']))<2e-6
for t in pack['textures']:
    blob=(folder/t['file']).read_bytes();assert blob==(ROOT/'build/tex'/(t['name']+'.bc')).read_bytes()
    assert t['mipsExported']==t['mipCount'];w,h=t['width'],t['height']
    for i,(offset,size) in enumerate(zip(t['mipOffset'],t['mipSize'])):
        decoded=decode_bc(blob[offset:offset+size],w,h,t['format']);assert decoded.shape==(h,w,4)
        if i==0:Image.fromarray(decoded).save(folder/'tex'/(t['name']+'.png'))
        w=max(w//2,1);h=max(h//2,1)
    texturechecks.append({'name':t['name'],'mips':t['mipCount'],'all_mips_decoded':True,'bytes_match':True})

rig=custom;native=parse_skeljson(rigdata);motions=[]
for label in ['idle','run','bow','riding','slash']:
    raw=json.loads((ROOT/'reports'/(label+'.json')).read_text());anim=parse_animjson(raw)
    assert raw['skeletonGuid']==native['guid'] and anim['have'].all() and anim['frames']>2
    frames=list(range(max(1,anim['start']),anim['frames'])) if label!='idle' else sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,16).astype(int).tolist()))
    worst=0;worstframe=frames[0];worstmesh='';percentile=0;meshstats=[]
    for m in exports[0]:
        tri=m['idx'].reshape(-1,3);edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
        base=np.linalg.norm(m['pos'][edges[:,0]]-m['pos'][edges[:,1]],axis=1);valid=base>.002;edges=edges[valid];base=base[valid]
        meshworst=0;meshp99=0
        for frame in frames:
            skin=skin_matrices(rig,anim,frame);p=lbs(m['pos'],m['bi'],m['bw'],skin);assert np.isfinite(p).all()
            ratio=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)/base
            if len(ratio):
                r=float(ratio.max());percentile=max(percentile,float(np.quantile(ratio,.99)))
                meshworst=max(meshworst,r);meshp99=max(meshp99,float(np.quantile(ratio,.99)))
                if r>worst:worst=r;worstframe=frame;worstmesh=m['name']
        meshstats.append({'name':m['name'],'max_extension':meshworst,'p99_extension':meshp99})
    # Reject gross tears; this guard does not certify absence of intersections.
    if worst>=6.0:
        (ROOT/'reports/motion_failure.json').write_text(json.dumps({'label':label,'mesh':worstmesh,'frame':worstframe,'max_extension':worst,'p99':percentile,'meshes':meshstats},indent=2))
    assert worst < 6.0, (label, worstmesh, worst, 'gross motion tear')
    motions.append({'label':label,'asset':raw['name'],'frames_checked':len(frames),'total_frames':anim['frames'],'worst_frame':worstframe,'worst_mesh':worstmesh,'max_edge_extension':worst,'max_mesh_p99_extension':percentile,'meshes':meshstats})

from verify_registration import validate_registration
registration=validate_registration(ROOT)
descriptor=ET.parse(ROOT/'module/YueQingShuRace/SubModule.xml')
assert descriptor.find('Id').get('value')=='YueQingShuRace' and descriptor.find('Version').get('value')==cfg['version']
assert sha(PACKAGE)==hash_before
assert all(sha(ROOT/p)==h for p,h in json.loads((ROOT/'reports/input_hashes.json').read_text()).items())
report={'version':cfg['version'],'status':'pass','check_scope':'offline_structural_and_native_motion_checks','final_package_sha256':hash_before,'baseline_package_sha256':'2de3a53994e0b137e8ea1f7188c086f3c9e6add9d3f2b8a455dd97d670632df1','baseline_reason':'v0.1.0 native-sized geometry replaced with source-proportioned custom skeleton','registration':registration,'lods':lods,'seams':seams,'motions':motions,'textures':texturechecks,'gross_motion_tear_guard_max_extension':6.0,'metadata_audit':'pass','game_test_verified':False,'game_cloth_solver_used':False,'limitations':['UE eye occlusion and tear overlays omitted; original default face/hair/clothes retained with conservative native materials.','Native motion scans do not prove weapon grip, horse collision, IK, all intersections or body slider compatibility.','No facial animation or face/body customization support.']}
report.update(integrated_hands_all_lods=True,cloth_enabled=False,body_metamesh='yqs_body',hidden_placeholder_triangles=4,source_proportions_preserved=True,custom_skeleton_bones=28)
(ROOT/'reports/release_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'registration':registration,'lods':lods,'seams':seams,'motions':motions},indent=2))
