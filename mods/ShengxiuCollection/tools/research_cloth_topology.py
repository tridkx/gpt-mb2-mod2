"""Native sample topology analysis; does not modify any package."""
from cloth_payload import *
from collections import Counter, defaultdict
import json


def inspect(path):
    data=read(path); ed=editor_read(path.with_suffix('.edit.bin'))
    mapping=data['render_to_sim']; nv=data['vertex_count']
    pos=np.zeros((nv,3)); pos[mapping]=ed['positions'][ed['vertices']['position']]
    tri=mapping[ed['faces']]
    active=data['max_distances']>0
    selected=tri[np.any(active[tri],axis=1)]
    edges=defaultdict(list)
    for a,b,c in tri:
        for i,j,k in [(a,b,c),(b,c,a),(c,a,b)]:edges[tuple(sorted((int(i),int(j))))].append(int(k))
    opposites={tuple(sorted(v)) for v in edges.values() if len(v)==2 and v[0]!=v[1]}
    types={name:[] for name in ['stretch','shear','bend','stitch']}
    conflicts=[]
    for s in data['constraint_sets']:
        indices=[]
        for k,name in enumerate(types):
            start,count=s[k*2:k*2+2]
            types[name].extend(data['constraints'][start:start+count].tolist())
            indices.extend(range(int(start),int(start+count)))
        assert len(indices)==len(set(indices))
        vertices=data['constraints'][indices].flatten()
        movable=vertices[vertices>=data['simulation_start']]
        conflicts.append(len(movable)-len(np.unique(movable)))
    summary={}
    for name,pairs in types.items():
        pairs=[tuple(sorted(pair)) for pair in pairs]
        summary[name]=dict(count=len(pairs),direct_edges=sum(p in edges for p in pairs),
                           opposite_vertices=sum(p in opposites for p in pairs),
                           fixed_fixed=sum(not active[a] and not active[b] for a,b in pairs))
    norms=np.linalg.norm(pos[data['constraints'][:,0]]-pos[data['constraints'][:,1]],axis=1)
    boundary=set(selected.ravel())-{int(i) for i in np.flatnonzero(active)}
    return dict(sample=path.name,bytes=len(path.read_bytes()),
        vertex_count=nv,render_count=len(mapping),triangles=len(tri),active_faces=len(selected),
        stored_dummy_faces=len(data['dummy_indices'])//3,
        starts=[data['simulation_start'],data['normal_start']],
        boundary_fixed_count=len(boundary),active_count=int(active.sum()),
        rest_position_error=float(np.linalg.norm(decode_positions(data)-pos,axis=1).max()),
        constraint_length_error=float(np.abs(norms-data['rest_lengths']).max()),
        alpha_error=float(np.abs(data['max_distances'][mapping]-ed['alpha']/255).max()),
        constraint_types=summary,parallel_set_conflicts=conflicts)


if __name__=='__main__':
    import sys
    rows=[inspect(Path(p)) for p in sys.argv[1:]]
    print(json.dumps(rows,indent=2))
