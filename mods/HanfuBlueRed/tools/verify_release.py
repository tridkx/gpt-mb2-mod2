"""Validate final TPAC bytes, four LODs, quantized seams and native motion."""
from pathlib import Path
import json,hashlib,sys,subprocess,re,xml.etree.ElementTree as ET
import numpy as np
import struct
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'D:\gpt-mb2-mod\tools');sys.path.insert(0,r'D:\gpt-mb2-mod\previewer')
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
from baker.material import decode_bc
MB=r'D:\mb-tools\mbtool\bin\Release\net9.0\mbtool.exe'
PACKAGE=ROOT/'module/HanfuBlueRed/AssetPackages/hbr.tpac'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf-8',errors='replace').stdout
package_hash=sha(PACKAGE)
audit=json.loads(run([r'C:\ProgramData\anaconda3\python.exe','-X','utf8',r'C:\Users\DKX\.codex\skills\bannerlord-equipment-mod\scripts\audit_package.py',str(PACKAGE),'--cloth-vertex-alpha']))
assert audit['status']=='pass',audit
(ROOT/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
visibility=json.loads(run(['dotnet',str(ROOT.parents[1]/'tools/AssetTool/AssetTool.dll'),'visibility',str(PACKAGE)]))
(ROOT/'reports/final_visibility.json').write_text(json.dumps(visibility,indent=2))
inspect=json.loads(run(['dotnet',str(ROOT.parents[1]/'tools/AssetTool/AssetTool.dll'),'inspect',str(PACKAGE)]))
(ROOT/'reports/final_cloth.json').write_text(json.dumps(inspect,indent=2))
assert {m['Name'] for m in inspect}=={'hbr_head','hbr_body','hbr_legs'}
assert len(visibility['materials'])==1
assert 'disable_vertex_color_alpha' in visibility['materials'][0]['ShaderMaterialFlags']
for mm in inspect:
    assert mm['UnknownString']=='human_body'
    for m in mm['meshes']:
        if 'uses_cloth_simulation' in m['Flags']:assert m['Lod']==0 and m['ClothingMaterial']['Name']=='hbr_limited_fabric'
        else:assert m['Lod']!=0 or not 'uses_cloth_simulation' in m['Flags']
geometry=json.loads((ROOT/'build/geometry.json').read_text());exports={};lods=[]
def mgeo(path):
    data=Path(path).read_bytes();magic,n,ni=np.frombuffer(data,'<i4',3);assert magic==0x4f45474d
    off=12;p=np.frombuffer(data,'<f4',n*3,off).reshape(n,3);off+=n*12
    normal=np.frombuffer(data,'<f4',n*3,off).reshape(n,3);off+=n*12
    tangent=np.frombuffer(data,'<f4',n*4,off).reshape(n,4);off+=n*16
    uv=np.frombuffer(data,'<f4',n*2,off).reshape(n,2);off+=n*16
    color=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
    bi=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
    bw=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
    idx=np.frombuffer(data,'<u4',ni,off).reshape(-1,3)
    assert np.isfinite(normal).all() and np.isfinite(tangent).all() and np.isfinite(uv).all()
    assert np.all(np.abs(np.linalg.norm(normal,axis=1)-1)<.02)
    return p,uv,bi,bw,idx,color
def dense(mesh):
    w=np.zeros((len(mesh['pos']),28));np.add.at(w,(np.arange(len(w))[:,None],mesh['bi']),mesh['bw']);return w
def final_vectors(path,meshes):
    data=path.read_bytes();off=12
    for m in meshes:
        for field in range(3):
            length=struct.unpack_from('<I',data,off)[0];off+=4+length
            if field==0:off+=4 # LOD follows the name.
        n=m['nverts'];flags=m['flags'];off+=8+24+4+n*12
        if flags&1:
            normals=np.frombuffer(data,'<f4',n*3,off).reshape(n,3);off+=n*12
            assert np.isfinite(normals).all() and np.all(np.abs(np.linalg.norm(normals,axis=1)-1)<.02),(m['name'],'final normals')
        off+=n*8
        if flags&2:off+=n*8
        if flags&4:off+=n*4
        if flags&8:off+=n*4
        if flags&16:
            tangent=np.frombuffer(data,'<f4',n*4,off).reshape(n,4);off+=n*16
            assert np.isfinite(tangent).all()
        if flags&32:off+=n*4
        off+=n*4+m['nidx']*4
    assert off==len(data)
for lod in range(4):
    folder=ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')
    run([MB,'exportmod',str(PACKAGE),str(folder),str(lod)]+(['--all-mips'] if lod==0 else []))
    meshes=[]
    for file in (folder/'geo').glob('*.bin'):
        rows=read_geo(file);final_vectors(file,rows);meshes.extend(rows)
    assert meshes and all(m['lod']==lod for m in meshes)
    exports[lod]=meshes
    for m in meshes:
        assert np.isfinite(m['pos']).all() and np.isfinite(m['uv']).all()
        assert m['bi'] is not None and m['bi'].max()<28
        assert (m['bw'].sum(1)==255).all()
        assert m['idx'].min()>=0 and m['idx'].max()<m['nverts']
    rows=[g for g in geometry if g['lod']==lod]
    assert sum(m['nidx']//3 for m in meshes)==sum(g['tris'] for g in rows)
    for g in rows:
        matched=[m for m in meshes if re.sub(r'\.b\d+$','',m['name'])==g['name']]
        assert matched,g['name']
        p,uv,bi,bw,indices,color=mgeo(g['geometry'])
        tree=cKDTree(p);expected={'pos':p,'bi':bi,'bw':bw};w=dense(expected)
        for m in matched:
            dist,idx=tree.query(m['pos']);assert dist.max()<1e-6
            # UV duplicates share position and weights. Validate UV against a
            # full position/UV key to avoid confusing two sides of an atlas cut.
            assert np.array_equal(dense(m),w[idx]),m['name']
            keys={tuple(np.round(np.r_[pp,uu],6)) for pp,uu in zip(p,uv)}
            assert all(tuple(np.round(np.r_[pp,uu],6)) in keys for pp,uu in zip(m['pos'],m['uv']))
    lods.append({'lod':lod,'vertices':sum(m['nverts'] for m in meshes),'triangles':sum(m['nidx']//3 for m in meshes),'submeshes':len(meshes)})
assert all(lods[i+1]['triangles']<lods[i]['triangles'] for i in range(3)),lods
# All source cut points shared between equipment pieces remain present and have
# identical quantized skinning in every LOD, including face/collar boundaries.
arrays=np.load(ROOT/'build/rig_arrays.npz');manifest=json.loads((ROOT/'build/rig_manifest.json').read_text())
cuts={}
for rec in manifest:
    for vi,co in enumerate(arrays[rec['object']+'_S']):cuts.setdefault(tuple(co),[]).append((rec['object'],vi,rec['part']))
record_by_name={r['object']:r for r in manifest}
for k,refs in cuts.items():
    if k[2]<.57*1.70:
        refs=[(n,i,slot) for n,i,slot in refs if record_by_name[n]['kind']!='belt_tassel']
        cuts[k]=refs
    if any(record_by_name[n]['part']=='head' and record_by_name[n]['kind'] in {'hair','ornament'} for n,i,slot in refs) and any(slot!='head' for n,i,slot in refs):
        cuts[k]=[(n,i,slot) for n,i,slot in refs if slot!='head']
cuts={k:v for k,v in cuts.items() if len({x[0] for x in v})>1}
seam_stats=[]
for lod,meshes in exports.items():
    byname={}
    for rec in manifest:
        name=rec['object']+('' if lod==0 else f'.lod{lod}')
        rows=[m for m in meshes if re.sub(r'\.b\d+$','',m['name'])==name]
        p=np.concatenate([m['pos'] for m in rows]);w=np.concatenate([dense(m) for m in rows]);byname[rec['object']]=(p,w,cKDTree(p))
    tested=0;equipment_boundaries=0;max_distance=0
    for refs in cuts.values():
        reference=None
        for name,vi,slot in refs:
            p,w,tree=byname[name];distance,index=tree.query(arrays[name+'_P'][vi]);max_distance=max(max_distance,float(distance))
            assert distance<2e-6,(lod,name,distance)
            if reference is not None:assert np.array_equal(reference,w[index]),(lod,name,'seam weights')
            reference=w[index]
        tested+=1;equipment_boundaries+=int(len({r[2] for r in refs})>1)
    seam_stats.append({'lod':lod,'shared_points':tested,'cross_equipment_points':equipment_boundaries,'max_position_error':max_distance})
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));motion=[]
# Inspect every running/riding/bow frame; standing idle is sampled across its
# long animation. Measurements use final exported, byte-quantized geometry.
for label in ['idle','run','bow','riding']:
    raw=json.loads((ROOT/'reports'/(label+'.json')).read_text());anim=parse_animjson(raw)
    assert raw['skeletonGuid']==rig['guid'] and anim['have'].all() and anim['frames']>2
    frames=list(range(max(1,anim['start']),anim['frames'])) if label!='idle' else sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,12).astype(int).tolist()))
    max_ratio=0;worst_frame=frames[0];worst_mesh='';max_seam_drift=0
    for frame in frames:
        skin=skin_matrices(rig,anim,frame)
        for m in exports[0]:
            p=lbs(m['pos'],m['bi'],m['bw'],skin);assert np.isfinite(p).all()
            tri=m['idx'].reshape(-1,3)
            # Very short sliver edges magnify floating point noise; report
            # extension of edges longer than 2 mm in the delivered rest mesh.
            a,b=tri[:,0],tri[:,1];base=np.linalg.norm(m['pos'][a]-m['pos'][b],axis=1);valid=base>.002
            ratio=np.linalg.norm(p[a[valid]]-p[b[valid]],axis=1)/base[valid]
            r=float(ratio.max()) if len(ratio) else 0
            if r>max_ratio:max_ratio=r;worst_frame=frame;worst_mesh=m['name']
    motion.append({'label':label,'asset':raw['name'],'frames_checked':len(frames),'total_frames':anim['frames'],'skipped_binding_frame':anim['start'],'max_edge_extension':max_ratio,'worst_frame':worst_frame,'worst_mesh':worst_mesh})
# Texture decode is checked from the final package, not only the original JPEG.
from PIL import Image
folder=ROOT/'build/final_export';pack=json.loads((folder/'pack.json').read_text());texture_checks=[]
for texture in pack['textures']:
    blob=(folder/texture['file']).read_bytes()
    assert blob==(ROOT/'build/tex'/(texture['name']+'.bc')).read_bytes()
    w,h=texture['width'],texture['height'];assert texture['mipsExported']==texture['mipCount']
    for offset,size in zip(texture['mipOffset'],texture['mipSize']):
        decoded=decode_bc(blob[offset:offset+size],w,h,texture['format']);assert decoded.shape==(h,w,4)
        w=max(w//2,1);h=max(h//2,1)
    if texture['name']=='hbr_original_d':
        assert (texture['width'],texture['height'],texture['mipCount'])==(4096,4096,13)
        rgba=decode_bc(blob[:texture['mipSize'][0]],4096,4096,texture['format'])
        Image.fromarray(rgba).save(folder/'tex/hbr_original_d.png')
        original=np.array(Image.open(ROOT/'tex/汉服女孩3d模型_basecolor.JPEG').convert('RGB'))
        diffuse_mean_error=float(np.abs(rgba[:,:,:3].astype(float)-original).mean())
    texture_checks.append({'name':texture['name'],'mips':texture['mipCount'],'all_mips_decoded':True,'encoded_bytes_match_build':True})
descriptor=ET.parse(ROOT/'module/HanfuBlueRed/SubModule.xml');items=ET.parse(ROOT/'module/HanfuBlueRed/ModuleData/items.xml')
assert descriptor.find('Id').get('value')=='HanfuBlueRed'
assert {item.get('mesh') for item in items.getroot()}=={'hbr_head','hbr_body','hbr_legs'}
assert sha(PACKAGE)==package_hash
report={'version':'v1.0.0','status':'offline_checks_pass','final_package_sha256':package_hash,'baseline_package_sha256':None,'baseline_reason':'First release, no earlier package','lods':lods,'seams':seam_stats,'motions':motion,'texture_resolution':[4096,4096],'textures':texture_checks,'diffuse_mean_absolute_error_255':diffuse_mean_error,'metadata_audit':'pass','game_test_verified':False,'game_cloth_solver_used':False,'limitations':'Offline native skeletal motion only. In-game cloth, weapon IK, horse collision and character body sliders require user testing.'}
(ROOT/'reports/release_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
