"""Prepare a shared skirt cage and preserve non-skirt cloth attachment islands.

All parameters and output paths belong to the explicitly selected mod.
"""
from pathlib import Path
import json,sys,re,uuid,subprocess,zipfile
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import gaussian_filter1d

def prepare(root):
    cfg=json.loads((root/'tools/model_config.json').read_text());cfg['mapped_cloth']=json.loads((root/'tools/skirt_proxy_config.json').read_text());policy=cfg['mapped_cloth'];prefix=cfg.get('prefix','yqs');build=root/'build'
    workspace=next(p for p in root.parents if (p/'tools/cloth_compiler').is_dir())
    sys.path.insert(0,str(workspace/'tools/asset_helpers/pipeline'))
    from build_assets import vertex_tangents
    source=np.load(build/'fitted_model.npz');paint=json.loads((root/'reports/cloth_paint.json').read_text())
    paint=paint if isinstance(paint,list) else paint['rows'];skirt_ids={};selected=[];selected_weights=[]
    for row in paint:
        skirt=[c['component'] for c in row['components'] if c['kind']=='skirt']
        if not skirt:continue
        name=row['object'];p=source[name+'_p'];faces=source[name+'_f']
        q,inv=np.unique(np.round(p,6) if prefix=='bmq' else p,axis=0,return_inverse=True);f=inv[faces]
        edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(q),len(q))),directed=False)
        mask=np.isin(labels[inv],skirt);skirt_ids[name]=(cKDTree(p),mask);selected.append(p[mask]);selected_weights.append(source[name+'_w'][mask])
        if name == 'yqs_part_10':
            main = max(skirt, key=lambda c: int((labels[inv] == c).sum()))
            primary = p[labels[inv] == main]
    skirt=np.concatenate(selected);transfer=json.loads((root/'reports/weight_transfer.json').read_text());bones=transfer['native_bones'];joints=np.array(transfer['source_landmarks']);pelvis=bones.index('pelvis')
    top=float(skirt[:,2].max());bottom=float(skirt[:,2].min())
    primary_mesh=json.loads((build/'simplified_primary_skirt.json').read_text())
    positions=np.array(primary_mesh['positions']);faces=primary_mesh['indices']
    columns=policy['columns'];rings=policy['rings']
    faces=np.array(faces,dtype=int);normals=np.zeros_like(positions)
    tri=positions[faces];fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    np.add.at(normals,faces.ravel(),np.repeat(fn,3,axis=0));normals/=np.linalg.norm(normals,axis=1)[:,None]
    alpha=np.minimum((top-positions[:,2])*policy['travel_slope'],policy['max_travel_m']);alpha[positions[:,2]>top-policy.get('root_band_m',.045)]=0;alpha[alpha<.008]=0
    # The attachment follows the original waistband weights; free lower rows
    # reference the pelvis, avoiding a lifted calf reference while running.
    nearest=cKDTree(skirt).query(positions)[1];dense=np.concatenate(selected_weights)[nearest].astype(float)
    blend=np.clip((top-positions[:,2])/.08,0,1);dense*=1-blend[:,None];dense[:,pelvis]+=blend
    bone=np.argsort(-dense,axis=1,kind='stable')[:,:4];values=np.take_along_axis(dense,bone,axis=1);values/=values.sum(1)[:,None]
    weight=np.floor(values*255).astype(int);weight[:,0]+=255-weight.sum(1)
    # Give active cage rows enough room to clear the actual collision union.
    capsules=json.loads((root/'reports/cloth_collision.json').read_text())['capsules'];needed=np.zeros(len(positions))
    for cap in capsules:
        a,b=np.array(cap['endpoints_m']);axis=b-a;t=np.clip((positions-a)@axis/(axis@axis),0,1)
        needed=np.maximum(needed,cap['radius_m']-np.linalg.norm(positions-a-t[:,None]*axis,axis=1))
    active=alpha>0;alpha[active]=np.maximum(alpha[active],needed[active]+.006)
    positions_list=[positions];normals_list=[normals];alpha_list=[np.rint(alpha*255)];bones_list=[bone];weights_list=[weight];faces_list=[faces]
    branches={'skirt':np.arange(len(faces)).tolist()};vertex_offset=len(positions);face_offset=len(faces)
    # Use a proven low LOD for other hanging parts. Each part keeps its own
    # attachment island; it shares no constraints with the skirt cage.
    manifests=json.loads((build/'cooked_cloth/manifest.json').read_text());pinned={x['guid']:x['solver_pinned_render_vertices'] for x in manifests}
    inputs=[]
    for path in (build/'cloth_final').glob('*.mesh.json'):
        m=json.loads(path.read_text());inputs.append(m)
    for m in inputs:
        if m['lod']!=policy['other_cloth_lod']:continue
        name=re.sub(r'\.lod\d+|\.b\d+','',m['name']);p=np.array(m['positions']);a=np.array(m['alpha'],float);a[pinned[m['guid']]]=0
        sk=np.zeros(len(p),bool)
        if name in skirt_ids:
            tree,mask=skirt_ids[name];dist,near=tree.query(p);assert dist.max()<.06, (name,float(dist.max()));sk=np.ones(len(p),bool) if prefix=='bmq' else mask[near]
        f=np.array(m['indices']).reshape(-1,3);keep=(a[f]>0).any(1)&~sk[f].any(1);f=f[keep]
        area=np.linalg.norm(np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]),axis=1);f=f[area>1e-10]
        if not len(f):continue
        ids=np.unique(f);owner=np.full(len(p),-1,int);owner[ids]=np.arange(len(ids));local=owner[f]
        positions_list.append(p[ids]);normals_list.append(np.array(m['normals'])[ids]);alpha_list.append(a[ids]);bones_list.append(np.array(m['bones'])[ids]);weights_list.append(np.array(m['weights'])[ids]);faces_list.append(local+vertex_offset)
        branches.setdefault(name,[]).extend(np.arange(face_offset,face_offset+len(f)).tolist());face_offset+=len(f);vertex_offset+=len(ids)
    mesh=dict(name=prefix+'_cloth_proxy',guid=str(uuid.uuid5(uuid.NAMESPACE_URL,cfg['id']+'/shared_cloth_proxy/mesh')),metamesh=prefix+'_cloth_proxy',lod=0,positions=np.concatenate(positions_list).tolist(),normals=np.concatenate(normals_list).tolist(),alpha=np.concatenate(alpha_list).astype(int).tolist(),bones=np.concatenate(bones_list).tolist(),weights=np.concatenate(weights_list).tolist(),indices=np.concatenate(faces_list).ravel().tolist(),skirt_vertices=list(range(len(positions))))
    p=np.array(mesh['positions']);n=np.array(mesh['normals']);f=np.array(mesh['indices']).reshape(-1,3);count=len(p)
    assert count<60000 and f.size<60000,('Proxy must stay in one native submesh',count,f.size)
    uv=np.zeros((count,2));t=vertex_tangents(p,f,uv,n);geo=build/'shared_cloth_proxy.mgeo'
    with geo.open('wb') as out:
        out.write(np.array([0x4f45474d,count,f.size],'<i4').tobytes())
        for value in [p,n,t,uv,uv]:out.write(np.asarray(value,'<f4').tobytes())
        colors=np.full((count,4),255,'u1');colors[:,3]=mesh['alpha']
        for value in [colors,mesh['bones'],mesh['weights']]:out.write(np.asarray(value,'u1').tobytes())
        out.write(f.astype('<u4').tobytes())
    (build/'proxy_source.json').write_text(json.dumps(mesh));(build/'proxy_branches.json').write_text(json.dumps(branches))
    proxy_geo=dict(name=mesh['name'],part='proxy',geometry=str(geo.resolve()),material=prefix+'_'+policy['material'].lower(),flags=[],materialFlags=['no_team_color','no_tattoo'],lod=0,vertices=count,triangles=len(f),cloth=True,kind='cloth')
    geometry=json.loads((build/'geometry.json').read_text());geometry=[g for g in geometry if g.get('part')!='proxy'];geometry.append(proxy_geo)
    (build/'mapped_geometry.json').write_text(json.dumps(geometry,indent=2))
    spec=json.loads((build/'spec.json').read_text());spec['output']=str((build/'mapped_base.tpac').resolve());spec['meshes']=[m for m in spec['meshes'] if m['name']!=mesh['metamesh']]
    spec['meshes'].append(dict(name=mesh['metamesh'],bodyPart='',template='mesh',groups=[{k:proxy_geo[k] for k in ['name','geometry','material','flags','materialFlags']}]))
    (build/'mapped_spec.json').write_text(json.dumps(spec,indent=2))
    report=dict(status='prepared',method='Simplified primary skirt surface drives layers; separate source attachment islands for other cloth',proxy_vertices=count,proxy_triangles=len(f),skirt_cage_vertices=len(positions),skirt_cage_triangles=len(faces),columns=columns,rings=rings,skirt_height_range_m=[bottom,top],pelvis_reference_bone=bones[pelvis],runtime_mapped=False,game_verified=False)
    (root/'reports/shared_proxy_preparation.json').write_text(json.dumps(report,indent=2));print('SHARED_PROXY_PREPARED',report)

if __name__=='__main__':prepare(Path(sys.argv[1]).resolve())
