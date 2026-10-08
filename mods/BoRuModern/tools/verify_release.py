"""Check final TPAC re-export, XML, all LODs, byte weights and native motion."""
from pathlib import Path
import json,hashlib,sys,subprocess,struct,re,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parents[1]
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/tools'));sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/previewer'))
from georead import read_geo as read_basic_geo
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
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe';PACKAGE=ROOT/'module/BoRuModern/AssetPackages/boru.tpac'
def read_geo(path):
    data=Path(path).read_bytes();off=12;meshes=read_basic_geo(path)
    def blob():
        nonlocal off
        size=struct.unpack_from('<i',data,off)[0];off+=4+size
    for m in meshes:
        blob();off+=4;blob();blob();off+=32
        flags=struct.unpack_from('<I',data,off)[0];off+=4;n=m['nverts'];off+=n*12
        assert flags&1,'Final normal stream missing'
        m['normal']=np.frombuffer(data,'<f4',n*3,off).reshape(n,3).copy();off+=n*12+n*8
        for flag,width in [(2,8),(4,4),(8,4),(16,16),(32,4)]:
            if flags&flag:off+=n*width
        off+=n*4+m['nidx']*4
        assert np.isfinite(m['normal']).all()
        assert (np.abs(np.linalg.norm(m['normal'],axis=1)-1)<.005).all()
    assert off==len(data)
    return meshes

def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf8',errors='replace').stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
hash_before=sha(PACKAGE)
audit=json.loads(run([sys.executable,'-B','-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(PACKAGE)]));assert audit['status']=='pass',audit
(ROOT/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
visible=json.loads(run(['dotnet',str(WORKSPACE/'tools/AssetTool/AssetTool.dll'),'visibility',str(PACKAGE)]))
(ROOT/'reports/final_visibility.json').write_text(json.dumps(visible,indent=2))
assert all('disable_vertex_color_alpha' in m['ShaderMaterialFlags'] for m in visible['materials'])
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
    meshes=[m for p in (folder/'geo').glob('*.bin') for m in read_geo(p)];exports[lod]=meshes
    assert meshes and all(m['lod']==lod for m in meshes)
    for m in meshes:
        assert np.isfinite(m['pos']).all() and np.isfinite(m['uv']).all()
        assert m['bi'] is not None and m['bi'].max()<28
        assert (m['bw'].sum(1)==255).all()
        assert m['idx'].min()>=0 and m['idx'].max()<m['nverts']
    rows=[g for g in geometry if g['lod']==lod];assert sum(m['nidx']//3 for m in meshes)==sum(g['triangles'] for g in rows)
    for g in rows:
        p,uv,bi,bw,idx=mgeo(g['geometry']);expected=dense({'pos':p,'bi':bi,'bw':bw});tree=cKDTree(p)
        matched=[m for m in meshes if re.sub(r'\.b\d+$','',m['name'])==g['name']];assert matched,g['name']
        for m in matched:
            dist,near=tree.query(m['pos']);assert dist.max()<2e-6
            assert np.array_equal(dense(m),expected[near]),m['name']
    lods.append({'lod':lod,'vertices':sum(m['nverts'] for m in meshes),'triangles':sum(m['nidx']//3 for m in meshes),'submeshes':len(meshes)})
assert all(lods[i+1]['triangles']<lods[i]['triangles'] for i in range(3)),lods

# Verify source points shared across different pieces/materials survived LOD
# reduction with matching quantized influences; exclude free-standing hair.
arrays=np.load(ROOT/'build/fitted_model.npz');manifest=json.loads((ROOT/'build/manifest.json').read_text());cuts={}
for rec in manifest:
    if rec['material']!='skin':continue
    for i,p in enumerate(arrays[rec['object']+'_p']):cuts.setdefault(tuple(np.round(p,5)),[]).append((rec['object'],i,rec['part']))
cuts={p:r for p,r in cuts.items() if len({n for n,i,part in r})>1};seams=[]
for lod,meshes in exports.items():
    byname={}
    for rec in manifest:
        name=rec['object']+('' if lod==0 else '.lod'+str(lod));rows=[m for m in meshes if re.sub(r'\.b\d+$','',m['name'])==name]
        p=np.concatenate([m['pos'] for m in rows]);w=np.concatenate([dense(m) for m in rows]);normal=np.concatenate([m['normal'] for m in rows]);byname[rec['object']]=(p,w,normal,cKDTree(p))
    tested=0;cross=0;drift=0;normal_drift=0
    for refs in cuts.values():
        ref=None;ref_normal=None
        for name,i,part in refs:
            p,w,normal,tree=byname[name];dist,near=tree.query(arrays[name+'_p'][i]);drift=max(drift,float(dist));assert dist<3e-6,(lod,name,dist)
            if ref is not None:assert np.array_equal(ref,w[near]),(lod,name,'seam weights')
            if ref_normal is not None:normal_drift=max(normal_drift,float(np.linalg.norm(ref_normal-normal[near])));assert np.linalg.norm(ref_normal-normal[near])<.003,(lod,name,'seam normals')
            ref_normal=normal[near];ref=w[near]
        tested+=1;cross+=int(len({part for name,i,part in refs})>1)
    seams.append({'lod':lod,'shared_points':tested,'cross_equipment_points':cross,'max_position_error':drift,'max_normal_difference':normal_drift})

rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));motions=[]
for label in ['idle','run','bow','riding']:
    raw=json.loads((ROOT/'reports'/(label+'.json')).read_text());anim=parse_animjson(raw)
    assert raw['skeletonGuid']==rig['guid'] and anim['have'].all() and anim['frames']>2
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
    assert worst < 6.0, (label, worstmesh, worst, 'gross motion tear')
    motions.append({'label':label,'asset':raw['name'],'frames_checked':len(frames),'total_frames':anim['frames'],'worst_frame':worstframe,'worst_mesh':worstmesh,'max_edge_extension':worst,'max_mesh_p99_extension':percentile,'meshes':meshstats})

folder=ROOT/'build/final_export_lod0';pack=json.loads((folder/'pack.json').read_text());texturechecks=[]
for t in pack['textures']:
    blob=(folder/t['file']).read_bytes();assert blob==(ROOT/'build/tex'/(t['name']+'.bc')).read_bytes()
    assert t['mipsExported']==t['mipCount'];w,h=t['width'],t['height']
    for i,(offset,size) in enumerate(zip(t['mipOffset'],t['mipSize'])):
        decoded=decode_bc(blob[offset:offset+size],w,h,t['format']);assert decoded.shape==(h,w,4)
        if i==0:Image.fromarray(decoded).save(folder/'tex'/(t['name']+'.png'))
        w=max(w//2,1);h=max(h//2,1)
    texturechecks.append({'name':t['name'],'mips':t['mipCount'],'all_mips_decoded':True,'bytes_match':True})
descriptor=ET.parse(ROOT/'module/BoRuModern/SubModule.xml');items=ET.parse(ROOT/'module/BoRuModern/ModuleData/items.xml')
assert descriptor.find('Id').get('value')=='BoRuModern' and descriptor.find('Version').get('value')=='v1.0.1'
assert {i.get('mesh') for i in items.getroot()}=={'boru_head','boru_body','boru_hands','boru_legs'}
assert sha(PACKAGE)==hash_before
assert all(sha(ROOT/p)==h for p,h in json.loads((ROOT/'reports/input_hashes.json').read_text()).items())
report={'version':'v1.0.1','status':'pass','check_scope':'offline_structural_and_native_motion_checks','final_package_sha256':hash_before,'baseline_package_sha256':'f7ca34965a9637fdf6add39f85e02b7f7ba41c12355b973ce6d6c91ed94fe01a','baseline_reason':'BoRuModern/v1.0.0: single-leg and single-shoe width revision','lods':lods,'seams':seams,'motions':motions,'textures':texturechecks,'gross_motion_tear_guard_max_extension':6.0,'metadata_audit':'pass','game_test_verified':False,'game_cloth_solver_used':False,'limitations':['Clothing ORM, mouth and accessory PBR unavailable; conservative documented fallback parameters used.','Native motion scans do not prove weapon grip, horse collision, IK, all intersections or body slider compatibility.','No facial animation or face/body customization support.']}
(ROOT/'reports/release_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'lods':lods,'seams':seams,'motions':motions},indent=2))
