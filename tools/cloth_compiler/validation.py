import numpy as np

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
