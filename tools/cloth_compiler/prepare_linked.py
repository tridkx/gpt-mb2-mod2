"""Preserve actual cloth surfaces and couple neighboring skirt layers."""
from pathlib import Path
import json,re,uuid,sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def prepare(root):
    cfg=json.loads((root/'tools/model_config.json').read_text());prefix=cfg.get('prefix','yqs');b=root/'build';policy=cfg['mapped_cloth'];workspace=next(p for p in root.parents if (p/'tools/cloth_compiler').is_dir());sys.path.insert(0,str(workspace/'tools/asset_helpers/pipeline'))
    from build_assets import vertex_tangents
    source=np.load(b/'fitted_model.npz');paint=json.loads((root/'reports/cloth_paint.json').read_text());paint=paint if isinstance(paint,list) else paint['rows'];lookup={}
    for row in paint:
        selected=[c['component'] for c in row['components'] if c['kind']=='skirt']
        if not selected:continue
        name=row['object'];p=source[name+'_p'];q,inv=np.unique(np.round(p,6) if prefix=='bmq' else p,axis=0,return_inverse=True);f=inv[source[name+'_f']];e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(e)),e.T),shape=(len(q),len(q))),directed=False)
        lookup[name]=(cKDTree(p),labels[inv],selected)
    pins={p['guid']:p['solver_pinned_render_vertices'] for p in json.loads((b/'cooked_cloth/manifest.json').read_text())};bones=json.loads((root/'reports/weight_transfer.json').read_text())['native_bones'];pelvis=bones.index('pelvis')
    rows=[]
    for path in (b/'cloth_final').glob('*.mesh.json'):
        m=json.loads(path.read_text())
        if m['lod']!=0:continue
        name=re.sub(r'\.lod\d+|\.b\d+','',m['name']);p=np.array(m['positions']);a=np.array(m['alpha'],float);a[pins[m['guid']]]=0;sk=np.zeros(len(p),bool);layer=np.full(len(p),-1,int)
        if name in lookup:
            tree,labels,selected=lookup[name];_,near=tree.query(p);layer=labels[near];sk=np.isin(layer,selected)
        f=np.array(m['indices']).reshape(-1,3);f=f[(a[f]>0).any(1)];area=np.linalg.norm(np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]),axis=1);f=f[area>1e-10];ids=np.unique(f)
        if not len(ids):continue
        owner=np.full(len(p),-1,int);owner[ids]=np.arange(len(ids));w=np.array(m['weights'],float)/255;bi=np.array(m['bones']);dense=np.zeros((len(p),len(bones)));np.add.at(dense,(np.arange(len(p))[:,None],bi),w)
        for component in np.unique(layer[sk]):
            target=sk&(layer==component)&(a>0);top=p[sk&(layer==component),2].max();distance=np.maximum(top-p[:,2],0);blend=np.clip(distance/.10,0,1)
            dense[target]*=1-blend[target,None];dense[target,pelvis]+=blend[target]
            a[target]=np.maximum(a[target],np.minimum(distance[target]*1.35,.85)*255)
        bi=np.argsort(-dense,axis=1,kind='stable')[:,:4];weights=np.take_along_axis(dense,bi,axis=1);weights/=weights.sum(1)[:,None];weights=np.floor(weights*255).astype(int);weights[:,0]+=255-weights.sum(1)
        rows.append(dict(name=name,p=p[ids],n=np.array(m['normals'])[ids],a=np.rint(a[ids]),bi=bi[ids],w=weights[ids],f=owner[f],sk=sk[ids],layer=layer[ids]))
    # Keep skirt vertices first for diagnostics, preserving every source surface.
    positions=[];normals=[];alphas=[];indices=[];weights=[];faces=[];branches={};layers={};vertex_offset=0;face_offset=0;skirt_vertices=[]
    for row in rows:
        p=row['p'];positions.append(p);normals.append(row['n']);alphas.append(row['a']);indices.append(row['bi']);weights.append(row['w']);faces.append(row['f']+vertex_offset)
        sf=row['sk'][row['f']].any(1);branches.setdefault('skirt',[]).extend((np.flatnonzero(sf)+face_offset).tolist());branches.setdefault(row['name'],[]).extend((np.flatnonzero(~sf)+face_offset).tolist())
        skirt_vertices.extend((np.flatnonzero(row['sk'])+vertex_offset).tolist())
        for layer in np.unique(row['layer'][row['sk']]):
            key=row['name']+'_'+str(layer);layers.setdefault(key,[]).extend((np.flatnonzero(row['sk']&(row['layer']==layer))+vertex_offset).tolist())
        vertex_offset+=len(p);face_offset+=len(row['f'])
    p=np.concatenate(positions);n=np.concatenate(normals);a=np.concatenate(alphas).astype(int);bi=np.concatenate(indices);w=np.concatenate(weights);f=np.concatenate(faces);count=len(p)
    assert count<60000 and f.size<60000,('Single proxy limit',count,f.size)
    # Triangular distance links preserve local separation and orientation. They
    # are native stretching constraints, not a claim of engine self-collision.
    base=max(layers,key=lambda key:len(layers[key]));base_ids=np.array(layers[base],int)
    base_mask=np.zeros(len(p),bool);base_mask[base_ids]=True
    branches['skirt_all']=branches['skirt'].copy();branches['skirt']=np.flatnonzero(base_mask[f].all(1)).tolist()
    _,unique_base=np.unique(np.round(p[base_ids],6),axis=0,return_index=True);base_ids=base_ids[unique_base]
    tree=cKDTree(p[base_ids]);links=[]
    for key,ids in layers.items():
        if key==base:continue
        target=np.array(ids,int);target=target[a[target]>0];distance,near=tree.query(p[target],k=3)
        for vertex,ds,neighbors in zip(target,distance,near):
            if ds[0]>.16:continue
            for d,index in zip(ds,neighbors):
                if d>.001:links.append([int(vertex),int(base_ids[index])])
    uv=np.zeros((count,2));t=vertex_tangents(p,f,uv,n);geo=b/'shared_cloth_proxy.mgeo'
    with geo.open('wb') as out:
        out.write(np.array([0x4f45474d,count,f.size],'<i4').tobytes())
        for value in [p,n,t,uv,uv]:out.write(np.asarray(value,'<f4').tobytes())
        color=np.full((count,4),255,'u1');color[:,3]=a
        for value in [color,bi,w]:out.write(np.asarray(value,'u1').tobytes())
        out.write(f.astype('<u4').tobytes())
    mesh=dict(name=prefix+'_cloth_proxy',guid=str(uuid.uuid5(uuid.NAMESPACE_URL,cfg['id']+'/shared_cloth_proxy/mesh')),metamesh=prefix+'_cloth_proxy',lod=0,positions=p.tolist(),normals=n.tolist(),alpha=a.tolist(),bones=bi.tolist(),weights=w.tolist(),indices=f.ravel().tolist(),skirt_vertices=skirt_vertices,layer_links=links,layers=layers)
    (b/'proxy_source.json').write_text(json.dumps(mesh));(b/'proxy_branches.json').write_text(json.dumps(branches))
    entry=dict(name=mesh['name'],part='proxy',geometry=str(geo.resolve()),material=prefix+'_'+policy['material'].lower(),flags=[],materialFlags=['no_team_color','no_tattoo'],lod=0,vertices=count,triangles=len(f),cloth=True,kind='cloth')
    geometry=[g for g in json.loads((b/'geometry.json').read_text()) if g.get('part')!='proxy'];geometry.append(entry);(b/'mapped_geometry.json').write_text(json.dumps(geometry,indent=2))
    spec=json.loads((b/'spec.json').read_text());spec['output']=str((b/'mapped_base.tpac').resolve());spec['meshes']=[m for m in spec['meshes'] if m['name']!=mesh['name']];spec['meshes'].append(dict(name=mesh['name'],bodyPart='',template='mesh',groups=[{k:entry[k] for k in ['name','geometry','material','flags','materialFlags']}]))
    (b/'mapped_spec.json').write_text(json.dumps(spec,indent=2))
    report=dict(status='prepared',method='Actual source cloth surfaces in a shared native proxy, with local inter-layer distance links',proxy_vertices=count,proxy_triangles=len(f),skirt_layers={key:len(ids) for key,ids in layers.items()},base_layer=base,candidate_layer_links=len(links),game_verified=False)
    (root/'reports/shared_proxy_preparation.json').write_text(json.dumps(report,indent=2));print('LINKED_SURFACE_PROXY',report)
