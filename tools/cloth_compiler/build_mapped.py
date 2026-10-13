"""Build an isolated mapped-cloth candidate; never overwrite a game module."""
from pathlib import Path
import sys,json,subprocess,hashlib,re
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from prepare_mapped import prepare
from cook_cloth import cook,batches
from cloth_payload import read,write as write_cloth,decode_positions
from mapping_payload import write,project,reconstruct

def run(args):subprocess.run([str(x) for x in args],check=True)

def build(root):
    cfg=json.loads((root/'tools/model_config.json').read_text());prefix=cfg.get('prefix','yqs');b=root/'build'
    workspace=next(p for p in root.parents if (p/'tools/cloth_compiler').is_dir());common=workspace/'tools/cloth_compiler'
    if cfg['mapped_cloth'].get('method')=='linked_surfaces':
        from prepare_linked import prepare as prepare_surface
        prepare_surface(root)
    else:prepare(root)
    run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','build',b/'mapped_spec.json'])
    run(['dotnet',b/'package_patch/PackagePatch.dll',b/'mapped_base.tpac',b/'mapped_uncooked.tpac',b/'mapped_geometry.json'])
    dump=b/'mapped_proxy_input';dump.mkdir(exist_ok=True)
    run(['dotnet',b/'cloth_probe/NativeClothProbe.dll',b/'mapped_uncooked.tpac',prefix+'_cloth_proxy','--dump-segments',dump])
    files=list(dump.glob('*.mesh.json'));assert len(files)==1
    mesh=json.loads(files[0].read_text());source_proxy=json.loads((b/'proxy_source.json').read_text())
    assert np.max(abs(np.array(mesh['positions'])-np.array(source_proxy['positions'])))<2e-7
    assert mesh['indices']==source_proxy['indices']
    # Coincident opposite card normals must not create a zero solver normal.
    p=np.array(mesh['positions']);n=np.array(mesh['normals']);keys=np.column_stack([p,mesh['alpha'],mesh['weights'],mesh['bones']]);_,inv=np.unique(keys,axis=0,return_inverse=True)
    sums=np.zeros((inv.max()+1,3));np.add.at(sums,inv,n)
    for index in np.flatnonzero(np.linalg.norm(sums,axis=1)<1e-5):
        ids=np.flatnonzero(inv==index);n[ids]=n[ids[0]]
    mesh['normals']=n.tolist()
    raw,plan=cook(mesh,dict(unanchored='pin_upper',axis=2,band_m=.008,min_vertices=2,reason='Retained upper attachment of source cloth island'))
    if source_proxy.get('layer_links'):
        data=read(raw);kind={}
        for group in data['constraint_sets']:
            for k,(start,count) in enumerate(group.reshape(4,2)):
                for edge in data['constraints'][start:start+count]:kind[tuple(sorted(map(int,edge)))]=k
        links=data['render_to_sim'][np.array(source_proxy['layer_links'],int)];added=0
        for a,z in links:
            edge=tuple(sorted([int(a),int(z)]))
            if a!=z and edge not in kind:kind[edge]=0;added+=1
        records=sorted(kind);sets=[];constraints=[]
        for group in batches(records,data['simulation_start']):
            row=[]
            for k in range(4):
                entries=[edge for edge in group if kind[edge]==k];row.extend([len(constraints),len(entries)]);constraints.extend(entries)
            sets.append(row)
        p_sim=np.zeros((data['vertex_count'],3));p_sim[data['render_to_sim']]=np.array(mesh['positions']);constraints=np.array(constraints,dtype='u2')
        data['constraints']=constraints;data['constraint_sets']=np.array(sets,dtype='i4');data['constraint_count']=len(constraints);data['rest_lengths']=np.linalg.norm(p_sim[constraints[:,0]]-p_sim[constraints[:,1]],axis=1).astype('f4')
        assert data['rest_lengths'].min()>1e-8
        raw=write_cloth(data);plan['sha256']=hashlib.sha256(raw).hexdigest();plan['linked_layer_constraints']=added;plan['stretch_constraints']=sum(k==0 for k in kind.values())
    cooked=b/'mapped_proxy_cooked';cooked.mkdir(exist_ok=True);path=cooked/(plan['guid']+'.bin');path.write_bytes(raw);plan['path']=str(path.resolve());(cooked/'manifest.json').write_text(json.dumps([plan],indent=2))
    run(['dotnet',b/'cloth_patch/ClothPatch.dll',b/'mapped_uncooked.tpac',cooked/'manifest.json',b/'mapped_proxy_ready.tpac','--allow-metameshes',prefix+'_cloth_proxy'])
    data=read(raw);sim_points=decode_positions(data);q=data['rest_normals'];sim_normals=np.column_stack([q>>21,(q>>10)&2047,q&1023])/np.array([2047,2047,1023])*2-1;sim_normals/=np.linalg.norm(sim_normals,axis=1)[:,None]
    triangles=data['render_to_sim'][np.array(mesh['indices']).reshape(-1,3)];branches=json.loads((b/'proxy_branches.json').read_text());source=np.load(b/'fitted_model.npz');paint=json.loads((root/'reports/cloth_paint.json').read_text());paint=paint if isinstance(paint,list) else paint['rows'];skirt_lookup={}
    for row in paint:
        selected=[c['component'] for c in row['components'] if c['kind']=='skirt']
        if not selected:continue
        name=row['object'];positions=source[name+'_p'];f=source[name+'_f'];keys=np.round(positions,6) if prefix=='bmq' else positions;unique,owner=np.unique(keys,axis=0,return_inverse=True);faces=owner[f];edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(unique),len(unique))),directed=False)
        skirt_lookup[name]=(cKDTree(positions),np.isin(labels[owner],selected),labels[owner])
    old_plans=json.loads((b/'cooked_cloth/manifest.json').read_text());old_pins={row['guid']:row['solver_pinned_render_vertices'] for row in old_plans}
    maps=b/'mapped_render_maps';maps.mkdir(exist_ok=True);manifest=[];report=[]
    for path in sorted((b/'cloth_final').glob('*.mesh.json')):
        render=json.loads(path.read_text());positions=np.array(render['positions']);active=np.array(render['alpha'])>0;unmapped=old_pins[render['guid']];active[unmapped]=False;name=re.sub(r'\.lod\d+|\.b\d+','',render['name']);mask=np.zeros(len(positions),bool)
        if name in skirt_lookup:
            tree,selection,source_components=skirt_lookup[name];_,source_nearest=tree.query(positions);mask=selection[source_nearest]
            if prefix=='bmq':mask[:]=True
            elif 'skirt_component_bounds' in cfg['mapped_cloth']:
                limits=cfg['mapped_cloth']['skirt_component_bounds'];unique,owner=np.unique(np.round(positions,6),axis=0,return_inverse=True)
                faces=owner[np.array(render['indices']).reshape(-1,3)];edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]);count,labels=connected_components(coo_matrix((np.ones(len(edges)),edges.T),shape=(len(unique),len(unique))),directed=False)
                for component in range(count):
                    ids=np.flatnonzero(labels[owner]==component);lo,hi=positions[ids].min(0),positions[ids].max(0)
                    if lo[2]>limits['minimum_bottom_m'] and hi[2]<limits['maximum_top_m'] and hi[2]-lo[2]>limits['minimum_height_m']:mask[ids]=True
        mi=np.zeros((len(positions),3),dtype='u2');mw=np.zeros((len(positions),4),dtype='f4');mw[:,0]=1
        for part,keep in [('skirt',active&mask),(name,active&~mask)]:
            ids=np.flatnonzero(keep)
            if not len(ids):continue
            assert part in branches,(render['name'],part,len(ids))
            local_tri=triangles[np.array(branches[part],int)]
            area=np.linalg.norm(np.cross(sim_points[local_tri[:,1]]-sim_points[local_tri[:,0]],sim_points[local_tri[:,2]]-sim_points[local_tri[:,0]]),axis=1)
            local_tri=local_tri[area>1e-9]
            local_vertices=np.unique(local_tri);vertex_tree=cKDTree(sim_points[local_vertices])
            # Batch to bound temporary N x candidate-triangle arrays.
            for batch in np.array_split(ids,max(1,(len(ids)+999)//1000)):
                distance,nearest=vertex_tree.query(positions[batch]);exact=distance<.00018
                matched=local_vertices[nearest[exact]];mi[batch[exact]]=matched[:,None];mw[batch[exact]]=np.array([1,0,0,0],dtype='f4')
                remaining=batch[~exact]
                if len(remaining):
                    i,w=project(positions[remaining],sim_points,sim_normals,local_tri)
                    if part=='skirt' and 'skirt_all' in branches:
                        error=np.linalg.norm(reconstruct(sim_points,sim_normals,i,w)-positions[remaining],axis=1)
                        fallback=(error>.0005)|(abs(w[:,3])>.025)|(np.maximum(-w[:,:3],0).max(1)>.15)
                        if fallback.any():
                            all_tri=triangles[np.array(branches['skirt_all'],int)];all_vertices=np.unique(all_tri);dist,near=cKDTree(sim_points[all_vertices]).query(positions[remaining[fallback]])
                            close=dist<.00018;fi=np.zeros((fallback.sum(),3),int);fw=np.zeros((fallback.sum(),4),'f4');fw[:,0]=1;fi[close]=all_vertices[near[close],None]
                            if (~close).any():fi[~close],fw[~close]=project(positions[remaining[fallback][~close]],sim_points,sim_normals,all_tri)
                            i[fallback]=fi;w[fallback]=fw
                    mi[remaining]=i;mw[remaining]=w
        if 'layers' in source_proxy and name in skirt_lookup:
            base_layer=json.loads((root/'reports/shared_proxy_preparation.json').read_text())['base_layer'];base_name,base_component=base_layer.rsplit('_',1)
            secondary=active&mask
            if name==base_name:secondary&=source_components[source_nearest]!=int(base_component)
            shared_ids=np.unique(triangles[np.array(branches['skirt'],int)])
            shared=secondary&np.isin(mi,shared_ids).all(1)&(mw[:,3]>=0)&(mw[:,3]<.0008)
            mw[shared,3]=.0008
        rebuilt=reconstruct(sim_points,sim_normals,mi[active],mw[active]);error=np.linalg.norm(rebuilt-positions[active],axis=1)
        assert error.max()<.001,(render['name'],float(error.max()))
        assert np.max(np.abs(mw[active,:3].sum(1)-1))<2e-6
        blob=write(mi,mw);dest=maps/(render['guid']+'.bin');dest.write_bytes(blob)
        manifest.append(dict(guid=render['guid'],path=str(dest.resolve()),sha256=hashlib.sha256(blob).hexdigest(),unmapped_vertices=unmapped,skirt_vertices=np.flatnonzero(active&mask).tolist()))
        report.append(dict(mesh=render['name'],lod=render['lod'],mapped_vertices=int(active.sum()),shared_skirt_vertices=int((active&mask).sum()),rest_reconstruction_max_error_m=float(error.max()),negative_offsets=int((mw[active,3]<-.003).sum()),maximum_absolute_offset_m=float(abs(mw[active,3]).max()),maximum_barycentric_extrapolation=float(np.maximum(-mw[active,:3],0).max())))
    (maps/'manifest.json').write_text(json.dumps(manifest,indent=2))
    patch=b/'mapped_patch';run(['dotnet','build',common/'MappedClothPatch.csproj','--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(b/'mapped_patch_obj')+'/', '-o',patch])
    native=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/EmAssetPackages/armor555/armor555.tpac')
    run(['dotnet',patch/'MappedClothPatch.dll',b/'mapped_proxy_ready.tpac',b/'mapped_candidate.tpac',maps/'manifest.json',prefix+'_body',prefix+'_cloth_proxy',native])
    (root/'reports/mapped_cloth_candidate.json').write_text(json.dumps(dict(status='candidate',proxy=plan,render_maps=report,final_candidate_sha256=hashlib.sha256((b/'mapped_candidate.tpac').read_bytes()).hexdigest(),game_verified=False,scope='One shared simulated cage preserves layer offsets; source non-skirt card islands retained; candidate not installed'),indent=2))
    print('MAPPED_CANDIDATE_READY',root.name,report)

if __name__=='__main__':build(Path(sys.argv[1]).resolve())
