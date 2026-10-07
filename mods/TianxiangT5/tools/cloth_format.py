"""Locally decoded Bannerlord 1.4.8 cloth segments; no editor dependency.

Types b97e0f10 (cooked fabric) and af41613e (render mapping). Native samples
are checked by byte-exact codec round trips and geometric constraint lengths.
"""
import io, struct
import numpy as np

FIELDS=[('lengths','<f4',1),('pairs','<u2',2),('batches','<u4',8),
        ('triangle_batches','<u4',2),('positions','<u4',1),('normals','<u4',1),
        ('render_to_particle','<u4',1),('triangles','<u4',1),('distances','<f4',1),
        ('inverse_mass','<f4',1),('bones','u1',1),('weights','<f4',1),('tethers','<u4',1)]

def read_cook(data):
    h=struct.unpack_from('<f5I8f',data); off=56; out={'header':h}
    for name,dtype,width in FIELDS:
        count=struct.unpack_from('<I',data,off)[0];off+=4
        size=count*width*np.dtype(dtype).itemsize
        assert off+size<=len(data),(name,count,off)
        a=np.frombuffer(data[off:off+size],dtype).copy();off+=size
        out[name]=a.reshape(-1,width) if width>1 else a
    assert off==len(data),(off,len(data))
    return out

def write_cook(c):
    out=io.BytesIO();out.write(struct.pack('<f5I8f',*c['header']))
    for name,dtype,width in FIELDS:
        a=np.array(c[name],dtype=dtype)
        out.write(struct.pack('<I',len(a)));out.write(a.tobytes())
    return out.getvalue()

def packed_positions(p):
    # Native compression uses fixed [-100,100] range and 21 bits per axis.
    assert np.max(np.abs(p))<100
    a=np.rint((p+100)/200*2097151).astype(np.uint64)
    v=(a[:,0]<<43)|(a[:,1]<<22)|(a[:,2]<<1)
    return np.column_stack([v>>32,v&0xffffffff]).astype('<u4').ravel()

def unpack_positions(raw):
    r=raw.astype(np.uint64).reshape(-1,2);v=(r[:,0]<<32)|r[:,1]
    return np.column_stack([(v>>s)&0x1fffff for s in [43,22,1]])*200/2097151-100

def pack_normals(n):
    a=np.clip(n,-1,1)
    x=np.rint((a[:,0]+1)*2047/2).astype(np.uint32)
    y=np.rint((a[:,1]+1)*2047/2).astype(np.uint32)
    z=np.rint((a[:,2]+1)*1023/2).astype(np.uint32)
    return (x<<21)|(y<<10)|z

def batches(items):
    """Greedy graph coloring: each batch has disjoint particle writes."""
    groups=[];used=[]
    for item in items:
        s=set(item)
        for i,u in enumerate(used):
            if not s&u: groups[i].append(item);u.update(s);break
        else:groups.append([item]);used.append(s)
    return groups

def cook(p,normal,faces,alpha,bones,weights):
    from scipy.spatial import cKDTree
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    p=np.asarray(p);normal=np.asarray(normal);faces=np.asarray(faces);alpha=np.asarray(alpha)
    n=len(p); assert n<65535 and np.isfinite(p).all()
    active_faces=faces[np.any(alpha[faces]>0,axis=1)]
    used=np.unique(active_faces);unused=np.setdiff1d(np.arange(n),used)
    assert np.all(alpha[unused]==0)
    fixed=used[alpha[used]==0];free=used[alpha[used]>0]
    order=np.r_[unused,fixed,free];inverse=np.empty(n,dtype=int);inverse[order]=np.arange(n)
    p=p[order];normal=normal[order];alpha=alpha[order]
    bones=np.array(bones)[order];weights=np.array(weights)[order]
    faces=inverse[active_faces]; fixed_count=len(unused)+len(fixed)
    edges={};opp=[]
    for tri in faces:
        for a,b,c in [(tri[0],tri[1],tri[2]),(tri[1],tri[2],tri[0]),(tri[2],tri[0],tri[1])]:
            edges.setdefault(tuple(sorted((int(a),int(b)))),[]).append(int(c))
    stretch=list(edges)
    for others in edges.values():
        if len(others)==2 and others[0]!=others[1]:opp.append(tuple(sorted(others)))
    bend=sorted(set(opp)-set(stretch))
    # Fully triangulated fabric needs stretch along all edges. Opposite vertices
    # across a shared edge provide distance bending; separate shear links omitted.
    # Color only particle endpoints, not the constraint category.
    colored=[];writes=[]
    for k,links in [(0,stretch),(2,bend)]:
        for a,b in links:
            for i,u in enumerate(writes):
                if a not in u and b not in u:colored[i].append((a,b,k));u.update((a,b));break
            else:colored.append([(a,b,k)]);writes.append({a,b})
    pairs=[];batch_rows=[]
    for batch in colored:
        row=[]
        for k in range(4):
            links=[(a,b) for a,b,kind in batch if kind==k]
            row.extend([len(pairs) if links else 0,len(links)]);pairs.extend(links)
        batch_rows.append(row)
    pairs=np.array(pairs);lengths=np.linalg.norm(p[pairs[:,0]]-p[pairs[:,1]],axis=1)
    triangle_groups=batches(faces.tolist());ordered_faces=[];tri_rows=[]
    for group in triangle_groups:
        tri_rows.append([len(group),len(ordered_faces)]);ordered_faces.extend(group)
    faces=np.array(ordered_faces)
    area=np.linalg.norm(np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]]),axis=1)/2
    mass=np.zeros(n)
    for k in range(3):np.add.at(mass,faces[:,k],area/3)
    imass=np.divide(1,mass,out=np.ones(n),where=mass>1e-10)
    e=np.array(stretch);graph=coo_matrix((np.ones(len(e)*2),(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(n,n))
    _,labels=connected_components(graph)
    anchors=np.arange(n);dist=np.zeros(n)
    for k in np.unique(labels):
        ids=np.flatnonzero(labels==k);roots=ids[ids<fixed_count]
        # Small skirt ornaments in the accepted source have no zero-alpha vertex.
        # Their skin-centered distance spheres still anchor them. Use a nearest
        # fixed particle for the auxiliary tether without changing their mask.
        if not len(roots):roots=np.arange(fixed_count)
        assert len(roots)>0,'No fixed particles available for tether generation'
        d,i=cKDTree(p[roots]).query(p[ids]);anchors[ids]=roots[i];dist[ids]=d
    scale=max(float(dist.max()/65535),1e-10)
    tethers=np.rint(dist/scale).astype(np.uint32)|(anchors.astype(np.uint32)<<16)
    header=(scale,len(pairs),n,fixed_count,len(unused),len(faces)*3,*p.min(0),1.,*p.max(0),1.)
    c={'header':header,'lengths':lengths,'pairs':pairs,'batches':batch_rows,'triangle_batches':tri_rows,
       'positions':packed_positions(p),'normals':pack_normals(normal),'render_to_particle':inverse,
       'triangles':faces.ravel(),'distances':alpha,'inverse_mass':imass,'bones':bones.ravel(),
       'weights':weights.ravel(),'tethers':tethers}
    data=write_cook(c);assert write_cook(read_cook(data))==data
    assert np.max(np.linalg.norm(unpack_positions(c['positions'])-p,axis=1))<.0002
    return data,inverse,p,normal

def write_mapping(indices,weights):
    ids=np.array(indices,dtype='<u2'); w=np.array(weights,dtype='<f4')
    assert ids.shape==(len(w),3) and w.shape[1]==4
    return struct.pack('<I',ids.size)+ids.tobytes()+struct.pack('<I',w.size)+w.tobytes()
