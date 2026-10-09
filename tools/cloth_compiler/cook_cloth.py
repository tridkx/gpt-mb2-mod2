"""Experimental offline cooker using the reverse engineered native layout.

Uses a triangle cloth network: mesh edges resist stretching; opposite vertices
of adjacent triangles resist bending. It does not reproduce native remeshing.
No constraints cross disconnected components or join different bone bindings.
"""
import json
import hashlib
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
try:
    from .cloth_payload import read, write
except ImportError:
    from cloth_payload import read, write


def batches(entries, immutable_end):
    """Greedy graph coloring; shader threads must never write the same vertex."""
    groups=[]; occupied=[]
    for entry in entries:
        touches={int(v) for v in entry if v>=immutable_end}
        for k,used in enumerate(occupied):
            if used.isdisjoint(touches):
                groups[k].append(entry);used.update(touches);break
        else:
            groups.append([entry]);occupied.append(touches)
    return groups


def encode_positions(pos):
    q=np.floor((pos+100)/200*0x1fffff).astype(np.uint64)
    assert np.all(q<=0x1fffff)
    x=(q[:,0]<<11)|(q[:,1]>>10)
    y=((q[:,1]&0x3ff)<<22)|(q[:,2]<<1)
    return np.column_stack((x,y)).astype('<u4').ravel()


def encode_normals(normals):
    q=np.floor(np.clip(normals*.5+.5,0,1)*[2047,2047,1023]).astype(np.uint32)
    return (q[:,0]<<21)|(q[:,1]<<10)|q[:,2]


def cook(mesh, root_policy=None):
    root_policy=root_policy or {'unanchored':'error'}
    p=np.asarray(mesh['positions'],float); normals=np.asarray(mesh['normals'],float)
    alpha=np.asarray(mesh['alpha'],np.uint8); weights=np.asarray(mesh['weights'],np.uint8)
    bones=np.asarray(mesh['bones'],np.uint8); faces=np.asarray(mesh['indices'],int).reshape(-1,3)
    skinned=weights.size>0
    assert p.ndim==2 and p.shape[1]==3 and len(p)>0 and np.isfinite(p).all()
    assert normals.shape==p.shape and np.isfinite(normals).all() and len(alpha)==len(p)
    assert not skinned or (weights.shape==bones.shape==(len(p),4) and np.all(weights.sum(1)==255))
    assert skinned or bones.size==0
    # Merge exact duplicates split for UV/normals; retain alpha and bone discontinuities.
    keys={}; representative=[]; render_map=[]
    for i in range(len(p)):
        key=(tuple(p[i]),int(alpha[i]),tuple(weights[i]) if skinned else (),tuple(bones[i]) if skinned else ())
        if key not in keys:keys[key]=len(keys);representative.append(i)
        render_map.append(keys[key])
    representative=np.asarray(representative); render_map=np.asarray(render_map)
    pos=p[representative]; a=alpha[representative].copy(); tri=render_map[faces]
    e=np.vstack((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]))
    connectivity=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(pos),len(pos))).tocsr()
    component_count,labels=connected_components(connectivity,directed=False)
    root_fixes=[]
    for component in range(component_count):
        ids=np.flatnonzero(labels==component)
        if np.any(a[ids]==0):continue
        action=root_policy.get('unanchored','error')
        if action=='freeze_small':
            assert len(ids)<=root_policy['max_positions'] and a[ids].max()<=root_policy['max_alpha'], 'Unanchored component exceeds explicit freeze limits'
            roots=ids;reason=root_policy.get('reason','keep explicitly permitted small component fixed')
        elif action=='pin_upper':
            band=root_policy['band_m'];axis=root_policy.get('axis',2);minimum=root_policy.get('min_vertices',2)
            assert band>=0 and axis in [0,1,2] and minimum>=1
            roots=ids[pos[ids,axis]>=pos[ids,axis].max()-band]
            if len(roots)<minimum:roots=ids[np.argsort(pos[ids,axis])[-min(minimum,len(ids)):]]
            reason=root_policy.get('reason','pin explicitly configured upper edge')
        else:raise ValueError(f"Unexpected unanchored component: {mesh['name']}")
        a[roots]=0
        root_fixes.append(dict(component_positions=len(ids),reason=reason,
                              pinned_render_vertices=np.flatnonzero(np.isin(render_map,roots)).tolist(),
                              bounds=[pos[ids].min(0).tolist(),pos[ids].max(0).tolist()]))
    active=a>0
    selected=tri[np.any(active[tri],axis=1)]
    boundary=np.unique(selected.ravel()); boundary=boundary[~active[boundary]]
    fixed=np.flatnonzero(~active)
    untouched=np.setdiff1d(fixed,boundary)
    permutation=np.concatenate((untouched,boundary,np.flatnonzero(active)))
    inverse=np.empty(len(pos),int);inverse[permutation]=np.arange(len(pos))
    pos=pos[permutation]; a=a[permutation]; tri=inverse[tri]; selected=inverse[selected]
    mapping=inverse[render_map]; representative=representative[permutation]
    sim_start=len(untouched);normal_start=len(fixed);nv=len(pos)
    assert 0<normal_start<nv<65536
    edgelist=defaultdict(list)
    for x,y,z in tri:
        if len({int(x),int(y),int(z)})<3:continue
        for i,j,k in [(x,y,z),(y,z,x),(z,x,y)]:
            edgelist[tuple(sorted((int(i),int(j))))].append(int(k))
    # Geodesic anchors use the full component graph, preserving fixed cuff roots.
    all_edges=np.asarray(sorted(edgelist),int)
    lengths=np.linalg.norm(pos[all_edges[:,0]]-pos[all_edges[:,1]],axis=1)
    ii=all_edges.ravel(); jj=all_edges[:,::-1].ravel(); ww=np.repeat(np.maximum(lengths,1e-10),2)
    graph=coo_matrix((ww,(ii,jj)),shape=(nv,nv)).tocsr()
    distance,_,anchor=dijkstra(graph,directed=False,indices=np.arange(normal_start),
                              min_only=True,return_predecessors=True)
    if not np.isfinite(distance).all():
        raise ValueError(f"{mesh['name']}: unanchored positions remain after root repair")
    scale=float(distance.max()/65535)
    anchors=(anchor.astype(np.uint32)<<16)|np.rint(distance/scale).clip(0,65535).astype(np.uint32)
    anchors[:normal_start]=np.arange(normal_start,dtype=np.uint32)<<16
    stretching=[tuple(e) for e in all_edges if np.any(a[e]>0)]
    bending=sorted({tuple(sorted(v)) for v in edgelist.values() if len(v)==2 and v[0]!=v[1]
                    and np.any(a[v]>0)}-set(stretching))
    records=[(edge,0) for edge in stretching]+[(edge,2) for edge in bending]
    groups=batches([e for e,_ in records],sim_start)
    kind={e:k for e,k in records}; constraints=[];sets=[]
    for group in groups:
        row=[]
        for k in range(4):
            entries=[e for e in group if kind[e]==k]
            row.extend([len(constraints),len(entries)]);constraints.extend(entries)
        sets.append(row)
    constraints=np.asarray(constraints,'<u2').reshape(-1,2)
    rest=np.linalg.norm(pos[constraints[:,0]]-pos[constraints[:,1]],axis=1).astype('<f4')
    assert np.all(rest>1e-8)
    dummy_groups=batches(selected.tolist(),sim_start);dummy=[];dummy_sets=[]
    for group in dummy_groups:
        dummy_sets.append([len(group),len(dummy)]);dummy.extend(group)
    dummy=np.asarray(dummy,'<u4').reshape(-1,3)
    areas=np.linalg.norm(np.cross(pos[tri[:,1]]-pos[tri[:,0]],pos[tri[:,2]]-pos[tri[:,0]]),axis=1)*.5
    sums=np.bincount(tri.ravel(),weights=np.repeat(areas,3),minlength=nv)
    inverse_area=np.divide(1,sums,out=np.zeros_like(sums),where=sums>1e-12)
    avg=np.zeros((nv,3)); np.add.at(avg,mapping,normals)
    normlen=np.linalg.norm(avg,axis=1);assert np.all(normlen>1e-5)
    avg/=normlen[:,None]
    result=dict(anchor_scale=scale,constraint_count=len(constraints),vertex_count=nv,
        normal_start=normal_start,simulation_start=sim_start,dummy_index_count=dummy.size,
        bounds=np.r_[pos.min(0),1,pos.max(0),1],rest_lengths=rest,constraints=constraints,
        constraint_sets=np.asarray(sets,'<i4'),dummy_sets=np.asarray(dummy_sets,'<i4'),
        rest_positions=encode_positions(pos),rest_normals=encode_normals(avg),
        render_to_sim=mapping.astype('<u4'),dummy_indices=dummy.ravel(),
        max_distances=(a.astype(np.float32)/255),inverse_areas=inverse_area.astype('<f4'),
        bone_indices=bones[representative].ravel() if skinned else np.empty(0,'u1'),
        bone_weights=(weights[representative].astype(np.float32)/255).ravel() if skinned else np.empty(0,'<f4'),anchors=anchors)
    raw=write(result);assert write(read(raw))==raw
    return raw,dict(mesh=mesh['name'],guid=mesh['guid'],metamesh=mesh['metamesh'],lod=mesh['lod'],
        bytes=len(raw),render_vertices=len(p),simulation_vertices=nv,fixed_positions=normal_start,
        boundary_fixed_positions=normal_start-sim_start,active_positions=nv-normal_start,
        stretch_constraints=len(stretching),bend_constraints=len(bending),
        shear_constraints=0,parallel_sets=len(sets),dummy_sets=len(dummy_sets),
        max_geodesic_anchor_length=float(distance.max()),sha256=hashlib.sha256(raw).hexdigest(),
        root_fixes=root_fixes,solver_pinned_render_vertices=np.flatnonzero((a[mapping]==0)&(alpha>0)).tolist())


def main(default_policy=None):
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--policy',type=Path,default=default_policy,help='Per-model unanchored-component policy; default rejects missing roots')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True);rows=[]
    policies=json.loads(args.policy.read_text(encoding='utf-8')) if args.policy else {}
    for path in sorted(args.input.glob('*.mesh.json')):
        mesh=json.loads(path.read_text());policy=policies.get('meshes',{}).get(mesh['name'],policies.get('default',{'unanchored':'error'}))
        raw,row=cook(mesh,policy);dest=args.output/(row['guid']+'.bin')
        dest.write_bytes(raw);row['path']=str(dest.resolve());rows.append(row)
        print(row['mesh'],row['simulation_vertices'],'positions',row['bytes'],'bytes')
    (args.output/'manifest.json').write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
