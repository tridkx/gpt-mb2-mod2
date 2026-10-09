"""Check native format evidence and generated payloads from final TPAC bytes.

Does not start Bannerlord; game acceptance and dynamics remain unverified.
"""
import hashlib
import json
import subprocess
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from cloth_payload import read, write, decode_positions
from research_cloth_topology import inspect

ROOT=Path(__file__).resolve().parents[1]
PROBE=ROOT/'build/cloth_probe/NativeClothProbe.dll'
BASE=ROOT/'build/cloth_baseline_v1.0.3'
PAYLOAD='b97e0f10-df49-4666-8f1d-ada6630d4b4e'
EDITOR='3d41985f-24d2-4fc1-82e4-6a6e0da3f4e2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def check_structure(data):
    nv=data['vertex_count'];nc=data['constraint_count'];ns=data['normal_start'];ss=data['simulation_start']
    assert 0<=ss<=ns<nv<65536
    assert len(data['rest_lengths'])==len(data['constraints'])==nc
    assert len(data['rest_positions'])==nv*2
    for key in ['rest_normals','max_distances','inverse_areas','anchors']:assert len(data[key])==nv
    assert len(data['bone_indices'])==len(data['bone_weights']) and len(data['bone_indices']) in [0,nv*4]
    assert len(data['dummy_indices'])==data['dummy_index_count'] and data['dummy_index_count']%3==0
    assert data['constraints'].max()<nv and data['render_to_sim'].max()<nv and data['dummy_indices'].max()<nv
    assert np.all(data['constraints'][:,0]!=data['constraints'][:,1])
    for key in ['rest_lengths','max_distances','inverse_areas','bone_weights']:assert np.isfinite(data[key]).all()
    assert np.all(data['rest_lengths']>0) and np.all(data['inverse_areas']>=0)
    assert np.all(data['max_distances'][:ns]==0) and np.all(data['max_distances'][ns:]>0)
    covered=[]
    for s in data['constraint_sets']:
        indices=[]
        # Shader processes all types as one contiguous range.
        expected=int(s[0])
        for start,count in s.reshape(4,2):
            if count:assert start==expected
            indices.extend(range(int(start),int(start+count)));expected+=int(count)
        vertices=data['constraints'][indices].ravel();mutable=vertices[vertices>=ss]
        assert len(mutable)==len(np.unique(mutable)), 'Parallel constraint write conflict'
        covered.extend(indices)
    assert sorted(covered)==list(range(nc))
    covered=[];tri=data['dummy_indices'].reshape(-1,3)
    for count,start in data['dummy_sets']:
        indices=list(range(int(start),int(start+count)));covered.extend(indices)
        vertices=tri[indices].ravel();mutable=vertices[vertices>=ss]
        assert len(mutable)==len(np.unique(mutable)), 'Parallel normal/collision write conflict'
    assert sorted(covered)==list(range(len(tri)))
    roots=data['anchors']>>16;dist=(data['anchors']&65535)*data['anchor_scale']
    assert roots.max()<ns and np.all(data['max_distances'][roots]==0)
    assert np.isfinite(dist).all() and data['anchor_scale']>0


def verify(package):
    if len([p for p in (ROOT/'build/cloth_segments').glob('*.bin') if '.edit.' not in p.name])<7:
        import sys
        subprocess.run([sys.executable,str(ROOT/'tools/extract_native_cloth_samples.py')],check=True)
    native_rows=[]
    for path in sorted((ROOT/'build/cloth_segments').glob('*.bin')):
        if '.edit.' in path.name:continue
        raw=path.read_bytes();data=read(raw);assert write(data)==raw
        check_structure(data)
        row=inspect(path)
        assert row['constraint_length_error']<2e-7 and row['alpha_error']<1e-6
        assert row['rest_position_error']<.00018
        assert row['active_faces']==row['stored_dummy_faces']
        row['sha256']=sha(path);row['byte_exact_roundtrip']=True;native_rows.append(row)
    assert len(native_rows)>=7
    out=ROOT/'build/final_cooked_cloth';out.mkdir(exist_ok=True)
    names=['sx_mingyu_head','sx_mingyu_body','sx_mingyu_legs']
    def probe(path,dump=False):
        command=['dotnet',str(PROBE),str(path),*names]
        if dump:command+=['--dump-segments',str(out)]
        return json.loads(subprocess.check_output(command,encoding='utf-8'))
    before=probe(BASE/'sx_mingyu.tpac');after=probe(package,True)
    manifest=json.loads((ROOT/'build/cooked_cloth/manifest.json').read_text())
    changes={r['guid']:r for r in manifest};mesh_count=0
    for mm in after:
        old=next(m for m in before if m['Guid']==mm['Guid'])
        assert {k:v for k,v in mm.items() if k not in ('meshes','segments')}=={k:v for k,v in old.items() if k not in ('meshes','segments')}
        for m in mm['meshes']:
            oldmesh=next(x for x in old['meshes'] if x['Guid']==m['Guid']);mesh_count+=1
            assert {k:v for k,v in m.items() if k!='edit_bones'}=={k:v for k,v in oldmesh.items() if k!='edit_bones'}
            if m['Guid'] in changes:assert m['edit_bones']==m['edit_positions']==m['SkinDataSize']
            else:assert m==oldmesh
        for s in old['segments']:
            current=next(t for t in mm['segments'] if t['TypeGuid']==s['TypeGuid'] and t['OwnerGuid']==s['OwnerGuid'])
            if s['TypeGuid']==EDITOR and s['OwnerGuid'] in changes:continue
            assert current==s, 'Unrelated data segment changed'
        assert len(mm['segments'])-len(old['segments'])==sum(r['metamesh']==mm['Name'] for r in manifest)
    assert mesh_count==56
    rows=[]
    for plan in manifest:
        path=out/(plan['metamesh']+'_'+plan['guid']+'.bin')
        raw=path.read_bytes();assert sha(path)==plan['sha256']
        data=read(raw);assert write(data)==raw;check_structure(data)
        mesh=json.loads((out/(plan['metamesh']+'_'+plan['guid']+'.mesh.json')).read_text())
        mapping=data['render_to_sim'];nv=data['vertex_count']
        p=np.asarray(mesh['positions']);pos=np.zeros((nv,3));pos[mapping]=p
        assert np.max(np.linalg.norm(decode_positions(data)[mapping]-p,axis=1))<.00018
        c=data['constraints'];length=np.linalg.norm(pos[c[:,0]]-pos[c[:,1]],axis=1)
        assert np.max(np.abs(length-data['rest_lengths']))<2e-7
        alpha=np.asarray(mesh['alpha'],np.float32)/255
        alpha[plan['solver_pinned_render_vertices']]=0
        assert np.max(np.abs(data['max_distances'][mapping]-alpha))<1e-6
        assert np.array_equal(data['bone_indices'].reshape(-1,4)[mapping],mesh['bones'])
        assert np.max(np.abs(data['bone_weights'].reshape(-1,4)[mapping]-np.asarray(mesh['weights'])/255))<1e-7
        assert np.max(np.abs(data['bone_weights'].reshape(-1,4).sum(1)-1))<1e-6
        tri=mapping[np.asarray(mesh['indices']).reshape(-1,3)]
        selected=tri[np.any(data['max_distances'][tri]>0,axis=1)]
        assert Counter(map(tuple,selected))==Counter(map(tuple,data['dummy_indices'].reshape(-1,3)))
        edges=np.vstack((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]))
        graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(nv,nv)).tocsr()
        _,labels=connected_components(graph,directed=False)
        assert np.all(labels==labels[data['anchors']>>16]), 'Anchor crosses disconnected components'
        assert np.all(labels[c[:,0]]==labels[c[:,1]])
        row=dict(plan);row.pop('path');row['from_final_tpac_sha256']=sha(path);rows.append(row)
    for file in ['ShengxiuCollection_Rigged.blend','ShengxiuCollection_Rigged.fbx']:
        assert sha(ROOT/'source'/file)==sha(BASE/file)
    report=dict(status='pass',final_package_sha256=sha(package),baseline_package_sha256=sha(BASE/'sx_mingyu.tpac'),
        native_samples=native_rows,cooked_meshes=rows,all_56_geometry_streams_and_indices_identical=True,
        all_runtime_alpha_and_skin_weights_preserved=True,editable_source_identical=True,
        unrelated_segments_identical=True,solver_root_overrides_explicit=True,
        limitations='Experimental triangle-network cooker; does not replicate the native remeshing algorithm. Native shader format and indices checked; engine acceptance and dynamics require user testing.',game_solver_verified=False)
    (ROOT/'reports/cooked_cloth_validation.json').write_text(json.dumps(report,indent=2))
    (ROOT/'reports/cloth_format_research.json').write_text(json.dumps(dict(status='pass',native_samples=native_rows,
        layout='float anchor_scale; 5 uint counters; 2 float4 bounds; 13 counted arrays',
        arrays=[name for name,_,_ in __import__('cloth_payload').FIELDS],
        source='Installed native TPAC samples and Shaders/Sources/gpucloth_solver.rs, shared_vertex_functions.rsh, definitions_shader_structs.rsh',
        exact_native_cooker_algorithm_reproduced=False),indent=2))
    print('COOKED_CLOTH_VERIFIED',len(rows),'meshes;',len(native_rows),'native byte-exact roundtrips; 56 geometry streams unchanged')
    return report


if __name__=='__main__':
    import sys
    verify(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac')
