"""Validate final TPAC bytes, decoded simulation, preservation and sources."""
from pathlib import Path
import hashlib,json,struct,subprocess
import numpy as np
from cloth_format import read_cook,write_cook,unpack_positions
from sleeve_motion import skin_frames,posed
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/mapped'
config=json.loads((ROOT/'tools/mapped_sleeves_config.json').read_text())
package=OUT/'tx5.tpac';dll=ROOT/'build/sleeve_tool/bin/SleeveTool.dll'
def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,encoding='utf-8').stdout
run(['dotnet',dll,'dump',package,OUT/'final.json'])
for name,folder in [('tx5_body','readback_body'),('tx5_cloth_simulation','readback_proxy')]:
    run(['dotnet',dll,'inspect',package,name,OUT/folder])
old={x['name']:x for x in json.loads((ROOT/'build/sleeve_final.json').read_text())}
new={x['name']:x for x in json.loads((OUT/'final.json').read_text())}
assert len(new)==len(old)+1 and set(new)-set(old)=={'tx5_cloth_simulation'}
changed={'tx5_body_00'}|{'tx5_body_00.lod'+str(lod) for lod in config['render_lods'] if lod}
disabled=set() if config['simulate_skirt'] else {'tx5_body_03'}
for name,m in old.items():
    if name in disabled:
        assert new[name]['flags']==[]
        assert {k:v for k,v in new[name].items() if k!='flags'}=={k:v for k,v in m.items() if k!='flags'}
    elif name not in changed:assert new[name]==m,name
    else:
        for key in m:
            if key not in ['color','flags']:assert new[name][key]==m[key],(name,key)
        assert new[name]['flags']==config['flags']
        assert np.array_equal(np.array(m['color'])[:,:3],np.array(new[name]['color'])[:,:3])
recipe=json.loads((OUT/'recipe.json').read_text())
for name in changed:assert [c[3] for c in new[name]['color']]==recipe['mapped'][name]['alpha']
body=json.loads((OUT/'readback_body/metadata.json').read_text())
proxy=json.loads((OUT/'readback_proxy/metadata.json').read_text())
assert body['ClothMetamesh']==proxy['Guid']==recipe['proxy_guid']
segment=next(s for s in proxy['segments'] if s['type'].startswith('b97'))
blob=(OUT/'readback_proxy'/segment['file']).read_bytes();assert blob==(OUT/'proxy_cooked.bin').read_bytes()
c=read_cook(blob);assert write_cook(c)==blob
n=c['header'][2];fixed=c['header'][3]
assert n==len(recipe['sources']) and fixed>0 and c['header'][1]==len(c['pairs'])
if not config['simulate_skirt']:
    assert n==284 and fixed==16
    assert all(s['mesh']=='tx5_body_00' for s in recipe['sources'])
    assert 'tx5_body_03' not in recipe['mapped']
    assert not any(s['type'].startswith('af416') and s['owner']==next(m['Guid'] for m in body['meshes'] if m['Name']=='tx5_body_03') for s in body['segments'])
assert c['header'][5]==len(c['triangles'])
for name in ['distances','inverse_mass','normals','tethers']:assert len(c[name])==n
assert len(c['bones'])==len(c['weights'])==n*4
assert c['pairs'].max()<n and c['triangles'].max()<n and c['render_to_particle'].max()<n
assert (c['tethers']>>16).max()<fixed
assert np.isfinite(c['lengths']).all() and np.all(c['lengths']>0)
assert np.isfinite(c['inverse_mass']).all() and np.all(c['inverse_mass']>0)
assert np.isfinite(c['weights']).all() and np.allclose(c['weights'].reshape(-1,4).sum(1),1)
assert c['bones'].max()<28
assert np.all(c['distances'][:fixed]==0)
p=np.array(new['tx5_cloth_simulation']['pos']);order=c['render_to_particle']
q=np.zeros_like(p);q[order]=p
assert np.max(np.linalg.norm(unpack_positions(c['positions'])-q,axis=1))<.0002
length_error=np.max(np.abs(np.linalg.norm(q[c['pairs'][:,0]]-q[c['pairs'][:,1]],axis=1)-c['lengths']))
assert length_error<1e-6
# Validate spatial ownership independently of the generating recipe: neither
# mappings, constraints nor tethers may join the two separate long sleeves.
assert np.all(q[c['pairs'][:,0],0]*q[c['pairs'][:,1],0]>0)
anchors=c['tethers']>>16
assert np.all(q[:,0]*q[anchors,0]>0)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
faces_for_edges=c['triangles'].reshape(-1,3)
edges=np.unique(np.sort(np.concatenate([faces_for_edges[:,[0,1]],faces_for_edges[:,[1,2]],faces_for_edges[:,[2,0]]]),axis=1),axis=0)
edge_lengths=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)
graph=coo_matrix((np.r_[edge_lengths,edge_lengths],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(n,n)).tocsr()
paths=dijkstra(graph,directed=False,indices=np.arange(fixed))
shortest=paths.min(axis=0)
quantized=(c['tethers']&65535)*c['header'][0]
tether_error=float(np.max(np.abs(quantized-shortest)))
assert tether_error<=c['header'][0]*1.1
assert np.allclose(paths[anchors,np.arange(n)],shortest,atol=1e-7)
covered=[]
for batch in c['batches'].reshape(-1,4,2):
    indices=np.concatenate([np.arange(s,s+count) for s,count in batch if count])
    particles=c['pairs'][indices].ravel();assert len(np.unique(particles))==len(particles)
    covered.extend(indices.tolist())
assert sorted(covered)==list(range(len(c['pairs'])))
triangle=c['triangles'].reshape(-1,3);covered=[]
for count,start in c['triangle_batches']:
    ids=triangle[start:start+count].ravel();assert len(np.unique(ids))==len(ids)
    covered.extend(range(start,start+count))
assert sorted(covered)==list(range(len(triangle)))
for name,settings in recipe['mapped'].items():
    guid=next(x['Guid'] for x in body['meshes'] if x['Name']==name)
    s=next(s for s in body['segments'] if s['owner']==guid and s['type'].startswith('af416'))
    raw=(OUT/'readback_body'/s['file']).read_bytes();assert raw==Path(settings['file']).read_bytes()
    count=struct.unpack_from('<I',raw)[0];assert count==len(new[name]['pos'])*3
    ids=np.frombuffer(raw[4:4+count*2],'<u2').reshape(-1,3)
    nw=struct.unpack_from('<I',raw,4+count*2)[0];assert nw==len(new[name]['pos'])*4
    w=np.frombuffer(raw[8+count*2:],'<f4').reshape(-1,4)
    assert ids.max()<n and np.isfinite(w).all() and np.max(np.abs(w[:,:3].sum(1)-1))<1e-5
    normals=np.zeros_like(p);normals[order]=new['tx5_cloth_simulation']['normal']
    rec=(q[ids]*w[:,:3,None]).sum(1)+(normals[ids]*w[:,:3,None]).sum(1)*w[:,3,None]
    active=np.array(settings['alpha'])>0
    tolerance=2e-6 if name=='tx5_body_00' else .02
    assert np.max(np.linalg.norm(rec[active]-np.array(new[name]['pos'])[active],axis=1))<tolerance
    assert w[active,:3].min()>=0 and w[active,:3].max()<=1
    assert np.all(np.array(new[name]['pos'])[active,0,None]*q[ids[active],0]>0)
for i,ref in enumerate(recipe['sources']):
    m=old[ref['mesh']];j=ref['index']
    assert new['tx5_cloth_simulation']['pos'][i]==m['pos'][j]
    assert new['tx5_cloth_simulation']['bi'][i]==m['bi'][j]
    assert new['tx5_cloth_simulation']['bw'][i]==m['bw'][j]
    distance=c['distances'][order[i]]*2
    scale=config['skirt_distance_scale'] if ref['mesh']=='tx5_body_03' else 1
    assert np.isclose(distance,m['color'][j][3]/255*m['multiplier']*scale,atol=1e-7)
assert new['tx5_cloth_simulation']['flags']==config['flags']
for key,value in config['material'].items():
    actual=new['tx5_cloth_simulation']['cloth'][key]
    assert actual==value if isinstance(value,str) else np.isclose(actual,value)
mbtool='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
segment_checks=[]
for name in ['tx5_body','tx5_cloth_simulation']:
    result=run([mbtool,'segcheck',package,name]);assert 'DIFFERS' not in result and 'first diff' not in result and 'failed' not in result
    segment_checks.append({'asset':name,'segments_roundtrip_identical':True})
audit=json.loads(run(['C:/ProgramData/anaconda3/python.exe','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',package,'--cloth-vertex-alpha']))
assert audit['status']=='pass';(ROOT/'reports/mapped_sleeves_asset_audit.json').write_text(json.dumps(audit,indent=2))
assettool=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/AssetTool/AssetTool.dll'
base=json.loads(run(['dotnet',assettool,'visibility',ROOT/'build/sleeve_baseline/tx5.tpac']))
final=json.loads(run(['dotnet',assettool,'visibility',package]));assert base['materials']==final['materials']
originals={x['Name']:x for x in base['meshes']}
for m in final['meshes']:
    if m['Name'] in originals and m['Name'] not in changed|disabled:
        # The hash includes the intentionally changed parent MetaMesh proxy GUID.
        excluded={'ClothMetadataSHA256'} if m['Name'].startswith('tx5_body_') else set()
        assert {k:v for k,v in m.items() if k not in excluded}=={k:v for k,v in originals[m['Name']].items() if k not in excluded},m['Name']
run([mbtool,'exportmod',package,OUT/'export','0','--all-mips'])
texture_hashes={}
for path in (ROOT/'build/sleeve_baseline/export/tex').glob('*.bin'):
    current=OUT/'export/tex'/path.name;assert current.read_bytes()==path.read_bytes()
    texture_hashes[path.name]=hashlib.sha256(current.read_bytes()).hexdigest()
assert len(texture_hashes)==11
source=json.loads((ROOT/'reports/sleeve_source_validation.json').read_text());assert source['status']=='pass'
for kind,filename in [('blend','TianxiangT5_Rigged.blend'),('fbx','TianxiangT5_Rigged.fbx')]:
    assert source[kind+'_sha256']==hashlib.sha256((ROOT/'source'/filename).read_bytes()).hexdigest()
rig=json.loads((ROOT/'reports/human_skeleton.json').read_text());motions=[]
for label in ['idle','run','bow','riding','grip_twohanded_block','grip_twohanded_thrust']:
    anim=json.loads((ROOT/f'reports/{label}.json').read_text());skins,_=skin_frames(rig,anim)
    for skin in skins:
        for name in ['tx5_body_00','tx5_body_00.lod1','tx5_cloth_simulation']:
            assert np.isfinite(posed(new[name],skin)).all()
    motions.append({'animation':anim['name'],'frames':len(skins)})
report={'version':config['version'],'status':'pass','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
        'route':'sleeve-only mapped simulation; skirt uses accepted skinning','unchanged_original_submeshes':len(old)-len(changed)-len(disabled),
        'original_geometry_and_skin_preserved':True,'proxy_particles':n,'constraints':len(c['pairs']),
        'constraint_length_max_error_m':float(length_error),'mapped_meshes':list(recipe['mapped']),
        'cross_sleeve_constraints_tethers_or_mappings':False,'convex_mapping_verified':True,
        'surface_tether_distance_max_error_m':tether_error,
        'byte_roundtrip':segment_checks,'all_materials_and_11_full_texture_mips_preserved':True,
        'texture_sha256':texture_hashes,'source_validation':'pass','native_animation_checks':motions,
        'material':config['material'],'force_cloth_flags_verified':True,'render_lods':config['render_lods'],'simulate_skirt':config['simulate_skirt'],'skirt_geometry_skin_and_vertex_stream_preserved':True,
        'game_solver_used':False,'game_test_verified':False,
        'limitations':'Skirt cloth is disabled after visible runtime stretching. Sleeve dynamics, NPC scheduling and riding collisions still require user game testing. Root cause of the former skirt mapping deformation is not yet uniquely established.'}
(ROOT/'reports/mapped_sleeves_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ['version','status','proxy_particles','constraints','mapped_meshes','final_package_sha256']},indent=2))
