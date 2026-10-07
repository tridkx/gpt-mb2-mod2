"""Verify independent fabric from the final package, never a construction cache."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components,dijkstra
from cloth_format import read_cook,write_cook,unpack_positions
from sleeve_motion import skin_frames,posed
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/direct_cloth'
config=json.loads((ROOT/'tools/direct_cloth_config.json').read_text());recipe=json.loads((OUT/'recipe.json').read_text())
package=OUT/'tx5.tpac';dll=ROOT/'build/sleeve_tool/bin/SleeveTool.dll'
def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,encoding='utf-8').stdout
run(['dotnet',dll,'dump',package,OUT/'final.json'])
old={m['name']:m for m in json.loads((ROOT/'build/sleeve_baseline/meshes.json').read_text())}
new={m['name']:m for m in json.loads((OUT/'final.json').read_text())}
assert old.keys()==new.keys() and len(new)==56
changed=set(recipe['meshes']);assert len(changed)==4
metadata={}
for owner in ['tx5_body','tx5_head','tx5_legs']:
    run(['dotnet',dll,'inspect',package,owner,OUT/owner])
    meta=json.loads((OUT/owner/'metadata.json').read_text());metadata[owner]=meta
    assert meta['ClothMetamesh']=='00000000-0000-0000-0000-000000000000'
    assert not any(s['type'].startswith('af416') for s in meta['segments'])
reports=[]
for name,m in new.items():
    p=np.array(m['pos']);bi=np.array(m['bi']);bw=np.array(m['bw']);faces=np.array(m['idx']).reshape(-1,3)
    assert np.isfinite(p).all() and np.isfinite(m['normal']).all() and faces.min()>=0 and faces.max()<len(p)
    assert bi.max()<28 and np.all(bw.sum(1)==255)
    if name not in changed:
        assert m==old[name],name;continue
    settings=recipe['meshes'][name]
    for k in m:
        if k not in ['color','flags','multiplier','cloth']:assert m[k]==old[name][k],(name,k)
    assert np.array_equal(np.array(m['color'])[:,:3],np.array(old[name]['color'])[:,:3])
    assert [c[3] for c in m['color']]==settings['alpha']
    assert m['flags']==['uses_cloth_simulation'] and m['body']=='human_body'
    assert np.isclose(m['multiplier'],settings['multiplier'])
    for k,v in settings['material'].items():assert m['cloth'][k]==v if isinstance(v,str) else np.isclose(m['cloth'][k],v)
    owner=next(k for k,v in metadata.items() if any(x['Name']==name for x in v['meshes']))
    guid=next(x['Guid'] for x in metadata[owner]['meshes'] if x['Name']==name)
    segs=[s for s in metadata[owner]['segments'] if s['owner']==guid and s['type'].startswith('b97')];assert len(segs)==1
    raw=(OUT/owner/segs[0]['file']).read_bytes();assert raw==Path(settings['cooked']).read_bytes()
    c=read_cook(raw);assert write_cook(c)==raw
    n=c['header'][2];fixed=c['header'][3];order=c['render_to_particle']
    metamesh=next(x for x in metadata[owner]['meshes'] if x['Name']==name)
    assert metamesh['PositionCount']==metamesh['SkinDataSize']==metamesh['EditPositionCount']==metamesh['EditBoneCount']==n
    assert metamesh['VertexCount']==len(p)
    assert len(order)==len(p) and set(order)==set(range(n))
    assert n<65535 and fixed>0 and c['header'][1]==len(c['pairs'])
    assert len(c['positions'])==n*2 and len(c['triangles'])==c['header'][5]
    for k in ['normals','distances','inverse_mass','tethers']:assert len(c[k])==n
    assert len(c['bones'])==len(c['weights'])==n*4
    q=np.zeros((n,3));q[order]=p
    assert np.max(np.linalg.norm(q[order]-p,axis=1))<2e-5
    assert np.max(np.linalg.norm(unpack_positions(c['positions'])-q,axis=1))<.0002
    assert np.array_equal(c['bones'].reshape(-1,4)[order],bi)
    assert np.allclose(c['weights'].reshape(-1,4)[order],bw/255,atol=1e-7)
    assert np.allclose(c['weights'].reshape(-1,4).sum(1),1)
    assert np.allclose(c['distances'][order],np.array(m['color'])[:,3]/255,atol=1e-7)
    assert np.all(c['distances'][:fixed]==0) and np.all(c['distances'][fixed:]>0)
    assert np.isfinite(c['inverse_mass']).all() and np.all(c['inverse_mass']>0)
    pairs=c['pairs'];tri=c['triangles'].reshape(-1,3)
    assert pairs.min()>=0 and pairs.max()<n and tri.max()<n
    err=float(np.max(np.abs(np.linalg.norm(q[pairs[:,0]]-q[pairs[:,1]],axis=1)-c['lengths'])))
    assert err<1e-6
    covered=[]
    for batch in c['batches'].reshape(-1,4,2):
        ids=np.concatenate([np.arange(s,s+count) for s,count in batch if count])
        particles=pairs[ids].ravel();assert len(set(particles))==len(particles);covered.extend(ids)
    assert sorted(covered)==list(range(len(pairs)))
    covered=[]
    for count,start in c['triangle_batches']:
        particles=tri[start:start+count].ravel();assert len(set(particles))==len(particles);covered.extend(range(start,start+count))
    assert sorted(covered)==list(range(len(tri)))
    edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
    lengths=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)
    g=coo_matrix((np.r_[lengths,lengths],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(n,n)).tocsr()
    _,labels=connected_components(g);anchors=c['tethers']>>16
    assert anchors.max()<fixed and np.all(labels==labels[anchors])
    assert np.all(labels[pairs[:,0]]==labels[pairs[:,1]])
    active=np.flatnonzero(c['distances']>0)
    paths=dijkstra(g,directed=False,indices=np.arange(fixed))[:,active]
    tether=(c['tethers']&65535)*c['header'][0]
    tether_error=float(np.max(np.abs(tether[active]-paths.min(0))))
    assert tether_error<c['header'][0]*1.1
    assert np.allclose(paths[anchors[active],np.arange(len(active))],paths.min(0),atol=1e-7)
    reports.append({'mesh':name,'particles':n,'active_particles':len(active),'render_vertices':len(p),'constraints':len(pairs),'maximum_distance_m':float(c['distances'].max()*m['multiplier']),'rest_constraint_max_error_m':err,'tether_quantization_max_error_m':tether_error,'no_cross_component_constraints_or_tethers':True,'render_particle_skin_and_alpha_consistent':True})
mbtool='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
for owner in metadata:
    text=run([mbtool,'segcheck',package,owner]);assert 'DIFFERS' not in text and 'failed' not in text and 'first diff' not in text
assettool=ROOT.parents[1]/'tools/AssetTool/AssetTool.dll'
audit=json.loads(run(['C:/ProgramData/anaconda3/python.exe','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',package,'--cloth-vertex-alpha']));assert audit['status']=='pass'
(ROOT/'reports/direct_cloth_asset_audit.json').write_text(json.dumps(audit,indent=2))
bv=json.loads(run(['dotnet',assettool,'visibility',ROOT/'build/sleeve_baseline/tx5.tpac']))
fv=json.loads(run(['dotnet',assettool,'visibility',package]));assert bv['materials']==fv['materials']
bvm={m['Name']:m for m in bv['meshes']}
for m in fv['meshes']:
    if m['Name'] not in changed:assert m==bvm[m['Name']],m['Name']
texture_hashes={}
run([mbtool,'exportmod',ROOT/'build/sleeve_baseline/tx5.tpac',ROOT/'build/sleeve_baseline/export','0','--all-mips'])
for lod in range(4):run([mbtool,'exportmod',package,OUT/('export_lod'+str(lod)),str(lod),'--all-mips'])
for tex in (ROOT/'build/sleeve_baseline/export/tex').glob('*.bin'):
    assert tex.read_bytes()==(OUT/'export_lod0/tex'/tex.name).read_bytes()
    texture_hashes[tex.name]=hashlib.sha256(tex.read_bytes()).hexdigest()
assert len(texture_hashes)==11
source=json.loads((ROOT/'reports/direct_source_validation.json').read_text());assert source['status']=='pass'
for kind in ['blend','fbx']:assert source[kind+'_sha256']==hashlib.sha256((ROOT/('source/TianxiangT5_Rigged.'+kind)).read_bytes()).hexdigest()
rig=json.loads((ROOT/'reports/human_skeleton.json').read_text());motions=[]
for label in ['idle','run','bow','riding','grip_twohanded_block','grip_twohanded_thrust']:
    anim=json.loads((ROOT/f'reports/{label}.json').read_text());skins,_=skin_frames(rig,anim)
    assert len(skins)>0
    for skin in skins:
        for m in new.values():assert np.isfinite(posed(m,skin)).all()
    motions.append({'animation':anim['name'],'valid_frames':len(skins),'all_four_lods_checked':True})
report={'version':config['version'],'status':'pass','baseline_package_sha256':config['baseline_sha256'],'final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'route':'independent cooked direct cloth; no external simulation mesh or mapping','cloth':reports,'unchanged_submeshes':len(new)-len(changed),'all_original_geometry_uv_normals_skin_preserved':True,'materials_and_11_full_mip_textures_preserved':True,'texture_sha256':texture_hashes,'source_validation':'pass','native_animation_checks':motions,'game_solver_used':False,'game_test_verified':False,'limitations':'Offline checks establish data consistency, not native cooker semantic equivalence or absence of runtime pulling. Sleeve LOD0/LOD1 and original skirt/hair LOD0 are simulated; farther LODs retain accepted skinning. No horse/self collision or NPC scheduling guarantee.'}
(ROOT/'reports/direct_cloth_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ['version','status','final_package_sha256','cloth','native_animation_checks']},indent=2))
