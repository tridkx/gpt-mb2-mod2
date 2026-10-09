"""Read final TPAC: structure, quantized geometry, skin seams, motion, textures."""
from pathlib import Path
import json,hashlib,sys,subprocess,re,struct,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/tools'));sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs,pose
def decode_bc(data,w,h,fmt):
    # Pillow's native BCN decoder supports the formats used by this package.
    if fmt=='BC5':im=Image.frombytes('RGB',(w,h),data,'bcn',(5,'BC5'))
    else:im=Image.frombytes('RGBA',(w,h),data,'bcn',(1 if fmt=='DXT1' else 3,fmt))
    return np.array(im.convert('RGBA'))
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe';PACKAGE=ROOT/'module/ShengxiuCollection/AssetPackages/sx_baifeng.tpac'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf-8',errors='replace').stdout
def dense(m):
    w=np.zeros((len(m['pos']),28),dtype=int);np.add.at(w,(np.arange(len(w))[:,None],m['bi']),m['bw']);return w
def read_mgeo(path):
    data=Path(path).read_bytes();magic,n,ni=np.frombuffer(data,'<i4',3);assert magic==0x4f45474d
    p=np.frombuffer(data,'<f4',n*3,12).reshape(n,3);uv=np.frombuffer(data,'<f4',n*2,12+n*40).reshape(n,2)
    normal=np.frombuffer(data,'<f4',n*3,12+n*12).reshape(n,3);tangent=np.frombuffer(data,'<f4',n*4,12+n*24).reshape(n,4)
    assert np.isfinite(normal).all() and np.isfinite(tangent).all() and np.isfinite(uv).all()
    assert np.all(abs(np.linalg.norm(normal,axis=1)-1)<.02)
    off=12+n*56;color=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
    bi=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4;bw=np.frombuffer(data,'u1',n*4,off).reshape(n,4)
    return {'pos':p,'uv':uv,'bi':bi,'bw':bw,'color':color}
def vectors_and_colors(path,meshes):
    data=path.read_bytes();off=12;result={}
    for m in meshes:
        for field in range(3):
            length=struct.unpack_from('<I',data,off)[0];off+=4+length
            if field==0:off+=4
        n=m['nverts'];flags=m['flags'];off+=8+24+4+n*12
        if flags&1:
            normal=np.frombuffer(data,'<f4',n*3,off).reshape(n,3);off+=n*12
            assert np.isfinite(normal).all() and np.all(abs(np.linalg.norm(normal,axis=1)-1)<.02)
        off+=n*8
        if flags&2:off+=n*8
        if flags&4:result[m['name']]=np.frombuffer(data,'u1',n*4,off).reshape(n,4);off+=n*4
        if flags&8:off+=n*4
        if flags&16:
            tangent=np.frombuffer(data,'<f4',n*4,off).reshape(n,4);off+=n*16;assert np.isfinite(tangent).all()
        if flags&32:off+=n*4
        off+=n*4+m['nidx']*4
    assert off==len(data);return result
package_hash=sha(PACKAGE)
audit=json.loads(run([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(PACKAGE),'--cloth-vertex-alpha']))
assert audit['status']=='pass',audit
(ROOT/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
visibility=json.loads(run(['dotnet',str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/AssetTool/AssetTool.dll'),'visibility',str(PACKAGE)]))
inspect=json.loads(run(['dotnet',str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/AssetTool/AssetTool.dll'),'inspect',str(PACKAGE)]))
(ROOT/'reports/final_visibility.json').write_text(json.dumps(visibility,indent=2));(ROOT/'reports/final_cloth.json').write_text(json.dumps(inspect,indent=2))
assert {mm['Name'] for mm in inspect}=={'sx_baifeng_head','sx_baifeng_body','sx_baifeng_legs'}
assert len(visibility['materials'])==9
for m in visibility['materials']:assert 'disable_vertex_color_alpha' in m['ShaderMaterialFlags']
for mm in inspect:
    assert mm['UnknownString']=='human_body'
    for m in mm['meshes']:
        if 'uses_cloth_simulation' in m['Flags']:
            assert m['Lod'] in [0,1]
            assert m['ClothingMaterial']['Name'] in ['sx_baifeng_skirt_fabric', 'sx_baifeng_long_hair_fabric', 'sx_baifeng_hanging_clothes_fabric']
geometry=json.loads((ROOT/'build/geometry.json').read_text());exports={};lods=[];seams=[]
fit=json.loads((ROOT/'reports/rig_fit.json').read_text());arrays=np.load(ROOT/'build/rig_arrays.npz')
for lod in range(4):
    folder=ROOT/'build'/('final_export' if lod==0 else f'final_export_lod{lod}')
    run([MB,'exportmod',str(PACKAGE),str(folder),str(lod)]+(['--all-mips'] if lod==0 else []))
    meshes=[];colors={}
    for file in (folder/'geo').glob('*.bin'):
        rows=read_geo(file);colors.update(vectors_and_colors(file,rows));meshes.extend(rows)
    assert len(meshes)==15 and all(m['lod']==lod for m in meshes)
    exports[lod]=meshes
    for m in meshes:
        assert np.isfinite(m['pos']).all() and np.isfinite(m['uv']).all()
        assert m['bi'] is not None and m['bi'].max()<28 and (m['bw'].sum(1)==255).all()
        assert m['idx'].min()>=0 and m['idx'].max()<m['nverts']
        base=re.sub(r'\.b\d+$','',m['name']);g=next(g for g in geometry if g['name']==base)
        expected=read_mgeo(g['geometry']);tree=cKDTree(expected['pos']);dist,idx=tree.query(m['pos']);assert dist.max()<1e-6
        assert np.array_equal(dense(m),dense(expected)[idx]),m['name']
        keys={tuple(np.round(np.r_[p,uv],6)) for p,uv in zip(expected['pos'],expected['uv'])}
        assert all(tuple(np.round(np.r_[p,uv],6)) in keys for p,uv in zip(m['pos'],m['uv']))
        # Coincident render vertices may intentionally have different cloth
        # distances at disconnected component roots; match all channels.
        def channelkeys(q,c):
            return {tuple(np.r_[np.round(p,6),np.round(uv,6),w,col]) for p,uv,w,col in zip(q['pos'],q['uv'],dense(q),c)}
        assert channelkeys(m,colors[m['name']])==channelkeys(expected,expected['color']),(m['name'],'runtime channels')
        if m['name']=='sx_baifeng_body_13':
            np.savez_compressed(ROOT/'build/final_sleeve_channels.npz',positions=m['pos'],colors=colors[m['name']],bone_indices=m['bi'],bone_weights=m['bw'])
        if m['name']=='sx_baifeng_body_13.lod1':
            np.savez_compressed(ROOT/'build/final_sleeve_channels_lod1.npz',positions=m['pos'],colors=colors[m['name']],bone_indices=m['bi'],bone_weights=m['bw'])
        assert m['nidx']//3==g['tris']
    lookup={re.sub(r'\.lod\d+$','',m['name']):(m,cKDTree(m['pos'])) for m in meshes}
    max_error=0
    for refs in fit['shared_skin_boundaries']:
        refw=None
        for name,vi in refs:
            m,tree=lookup[name];dist,index=tree.query(arrays[name+'_P'][vi]);assert dist<2e-6
            max_error=max(max_error,float(dist));w=dense(m)[index]
            if refw is not None:assert np.array_equal(refw,w),(lod,name,'skin seam')
            refw=w
    seams.append({'lod':lod,'shared_skin_points':len(fit['shared_skin_boundaries']),'max_position_error':max_error})
    lods.append({'lod':lod,'vertices':sum(m['nverts'] for m in meshes),'triangles':sum(m['nidx']//3 for m in meshes)})
assert all(lods[i+1]['triangles']<lods[i]['triangles'] for i in range(3))
vectors_colors={}
for f in (ROOT/'build/final_export/geo').glob('*.bin'):vectors_colors.update(vectors_and_colors(f,read_geo(f)))
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));motion=[]
for label in ['idle','run','bow','riding']:
    raw=json.loads((ROOT/'reports'/(label+'.json')).read_text());anim=parse_animjson(raw)
    assert raw['skeletonGuid']==rig['guid'] and anim['have'].all() and anim['frames']>2
    frames=list(range(max(1,anim['start']),anim['frames'])) if label!='idle' else sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,16).astype(int).tolist()))
    maximum=0;worst_frame=frames[0];worst_mesh='';maxp99=0;fixed_max=0;fixed_p99=0
    deepest=0;contact_frame=frames[0];contact_samples=0
    for frame in frames:
        skin=skin_matrices(rig,anim,frame)
        for m in exports[0]:
            p=lbs(m['pos'],m['bi'],m['bw'],skin);assert np.isfinite(p).all()
            tri=m['idx'].reshape(-1,3);edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);a,b=edges.T
            length=np.linalg.norm(m['pos'][a]-m['pos'][b],axis=1);valid=length>.003
            ratio=np.linalg.norm(p[a[valid]]-p[b[valid]],axis=1)/length[valid]
            distance=vectors_colors[m['name']][:,3]
            fixed=(distance[a[valid]]==0)&(distance[b[valid]]==0)
            if np.any(fixed):fixed_max=max(fixed_max,float(ratio[fixed].max()));fixed_p99=max(fixed_p99,float(np.quantile(ratio[fixed],.99)))
            r=float(ratio.max()) if len(ratio) else 0;maxp99=max(maxp99,float(np.quantile(ratio,.99)) if len(ratio) else 0)
            if r>maximum:maximum=r;worst_frame=frame;worst_mesh=m['name']
            if m['name'] in {r['object'] for r in fit['parts'] if r['kind']=='skirt'}:
                # Vertices and triangle centres against approximate native leg
                # capsules: diagnostic only, no game cloth solver is involved.
                points=np.concatenate([p,p[tri].mean(1)]);joints=pose(rig,anim,frame)[:,:3,3]
                gap=[]
                for start,end,radius in [(1,2,.075),(2,3,.050),(5,6,.075),(6,7,.050)]:
                    a=joints[start];axis=joints[end]-a;t=np.clip((points-a)@axis/(axis@axis),0,1)
                    gap.append(np.linalg.norm(points-a-t[:,None]*axis,axis=1)-radius)
                depth=max(0,-float(np.min(gap)));contact_samples=max(contact_samples,int((np.min(gap,axis=0)<0).sum()))
                if depth>deepest:deepest=depth;contact_frame=frame
    # Coarse rejection of catastrophic skin stretching, supplementing visual QA.
    print('MOTION_DIAGNOSTIC',label,maximum,maxp99,worst_mesh,worst_frame,flush=True)
    assert fixed_max<4 and fixed_p99<3,(label,'excessive fixed skin deformation',fixed_max,fixed_p99,worst_mesh,worst_frame)
    motion.append({'label':label,'asset':raw['name'],'frames_checked':len(frames),'total_frames':int(anim['frames']),'max_edge_extension':maximum,'max_p99_edge_extension':maxp99,'fixed_max_edge_extension':fixed_max,'fixed_max_p99_edge_extension':fixed_p99,'cloth_skinning_diagnostic_only':True,'worst_frame':int(worst_frame),'worst_mesh':worst_mesh,'skirt_leg_proxy':{'deepest_overlap_m':deepest,'worst_frame':int(contact_frame),'maximum_contact_samples':contact_samples,'method':'skirt vertices and triangle centres vs 75mm thigh / 50mm calf capsules; diagnostic only'}})
# Decode every mip from final bytes; compare input alpha and colour for all maps.
folder=ROOT/'build/final_export';pack=json.loads((folder/'pack.json').read_text());textures=[]
cfg=json.loads((ROOT/'tools/model_config.json').read_text())
for tex in pack['textures']:
    blob=(folder/tex['file']).read_bytes();assert blob==(ROOT/'build/tex'/(tex['name']+'.bc')).read_bytes()
    assert tex['mipsExported']==tex['mipCount'];w,h=tex['width'],tex['height'];base=None
    for off,size in zip(tex['mipOffset'],tex['mipSize']):
        decoded=decode_bc(blob[off:off+size],w,h,tex['format']);assert decoded.shape==(h,w,4)
        if base is None:base=decoded
        w=max(1,w//2);h=max(1,h//2)
    Image.fromarray(base).save(folder/'tex'/(tex['name']+'.png'))
    entry={'name':tex['name'],'mips':tex['mipCount'],'decoded_all_mips':True}
    key=tex['name'].removeprefix('sx_baifeng_').removesuffix('_d')
    if key in cfg['textures']:
        original=np.array(Image.open(ROOT/'tex'/cfg['textures'][key][0]).convert('RGBA'))
        assert original.shape==base.shape
        entry['rgb_mean_error_255']=float(np.abs(base[:,:,:3].astype(float)-original[:,:,:3]).mean())
        entry['alpha_mean_error_255']=float(np.abs(base[:,:,3].astype(float)-original[:,:,3]).mean())
    textures.append(entry)
descriptor=ET.parse(ROOT/'module/ShengxiuCollection/SubModule.xml');items=ET.parse(ROOT/'module/ShengxiuCollection/ModuleData/items.xml')
assert descriptor.find('Name').get('value').isascii() and descriptor.find('Id').get('value')=='ShengxiuCollection'
assert {i.get('mesh') for i in items.getroot()}=={'sx_baifeng_head','sx_baifeng_body','sx_baifeng_legs'}
assert sha(PACKAGE)==package_hash
report={'version':descriptor.find('Version').get('value'),'status':'pass','check_scope':'offline_checks','final_package_sha256':package_hash,'baseline_package_sha256':None,'baseline_reason':'new set, original inputs retained','lods':lods,'seams':seams,'motions':motion,'textures':textures,'metadata_audit':'pass','game_test_verified':False,'game_cloth_solver_used':False,'limitations':'Offline native skeletal motion. In-game cloth, weapon IK, face animation, body sliders and horse collision require user testing.'}
(ROOT/'reports/release_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'lods':lods,'motions':motion,'status':report['status']},indent=2))
