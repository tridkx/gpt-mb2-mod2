"""Compile a model-specific shared hair proxy and map all selected hair LODs."""
from pathlib import Path
import json,sys,subprocess,hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from context import config,workspace_root

def build_cloth(root):
    c=config(root);w=workspace_root(root);b=root/'build';prefix=c['prefix'];common=w/'tools/cloth_compiler';sys.path[:0]=[str(common),str(w/'tools/asset_helpers/pipeline')]
    from build_assets import vertex_tangents
    from cook_cloth import cook
    from cloth_payload import read,decode_positions
    from mapping_payload import project,write,reconstruct
    def run(args):
        result=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf8',errors='replace')
        with (b/'cloth_build.log').open('a',encoding='utf8') as log:log.write(result.stdout+result.stderr)
        if result.returncode:raise RuntimeError(result.stdout[-3000:]+result.stderr[-3000:])
    source=np.load(b/'fitted_model.npz');manifest=json.loads((b/'manifest.json').read_text(encoding='utf8'));points=[];normals=[];alphas=[];dense=[];faces=[];off=0
    for rec in manifest:
        if rec['source_material_index'] not in c['cloth_proxy_materials']:continue
        p=source[rec['object']+'_p'];f=source[rec['object']+'_f'];a=source[rec['object']+'_alpha'];ww=source[rec['object']+'_w']
        # Weld only coincident source positions; no shape fitting or widening.
        q,owner=np.unique(np.round(p,6),axis=0,return_inverse=True);ff=owner[f];aa=np.zeros(len(q));np.maximum.at(aa,owner,a);weights=np.zeros((len(q),28));np.add.at(weights,owner,ww);weights/=np.bincount(owner)[:,None]
        canonical=np.sort(ff,axis=1);_,keep=np.unique(canonical,axis=0,return_index=True);ff=ff[np.sort(keep)];area=np.linalg.norm(np.cross(q[ff[:,1]]-q[ff[:,0]],q[ff[:,2]]-q[ff[:,0]]),axis=1);ff=ff[area>1e-10]
        e=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(e)),e.T),shape=(len(q),len(q))),directed=False);accepted=[]
        for k in np.unique(labels):
            ids=np.flatnonzero(labels==k);has_root=bool((aa[ids]==0).any());height=float(np.ptp(q[ids,2]))
            if has_root or height>=c['cloth_proxy_policy']['minimum_component_height_m']:accepted.extend(ids.tolist())
        accepted=np.array(accepted);keep=np.isin(ff,accepted).all(1);ff=ff[keep];ids=np.unique(ff);lookup=np.full(len(q),-1,int);lookup[ids]=np.arange(len(ids));ff=lookup[ff];q=q[ids];aa=aa[ids];weights=weights[ids]
        n=np.zeros_like(q);tri=q[ff];fn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);np.add.at(n,ff.ravel(),np.repeat(fn,3,axis=0));bad=np.linalg.norm(n,axis=1)<1e-9;n[bad]=[0,-1,0];n/=np.linalg.norm(n,axis=1)[:,None]
        points.append(q);normals.append(n);alphas.append(aa);dense.append(weights);faces.append(ff+off);off+=len(q)
    p=np.concatenate(points);n=np.concatenate(normals);a=np.rint(np.concatenate(alphas)*255).astype('u1');ww=np.concatenate(dense);f=np.concatenate(faces);assert len(p)<60000 and f.size<60000,(c['id'],len(p),f.size)
    bi=np.argsort(-ww,axis=1)[:,:4];values=np.take_along_axis(ww,bi,axis=1);values/=values.sum(1)[:,None];bw=np.floor(values*255).astype(int);bw[:,0]+=255-bw.sum(1);uv=np.zeros((len(p),2));t=vertex_tangents(p,f,uv,n);geo=b/'hair_proxy.mgeo'
    with geo.open('wb') as out:
        out.write(np.array([0x4f45474d,len(p),f.size],'<i4').tobytes())
        for v in [p,n,t,uv,uv]:out.write(np.asarray(v,'<f4').tobytes())
        color=np.full((len(p),4),255,'u1');color[:,3]=a
        for v in [color,bi,bw]:out.write(np.asarray(v,'u1').tobytes())
        out.write(f.astype('<u4').tobytes())
    from proxy_material import add_material
    spec=json.loads((b/'spec.json').read_text());invisible=add_material(root,spec);(b/'spec.json').write_text(json.dumps(spec,indent=2))
    proxy=dict(name=prefix+'_cloth_proxy',part='proxy',geometry=str(geo),material=invisible,flags=[],materialFlags=['no_team_color','no_tattoo'],lod=0,vertices=len(p),triangles=len(f),cloth=True)
    geometry=json.loads((b/'geometry.json').read_text());geometry=[g for g in geometry if g['part']!='proxy'];geometry.append(proxy);(b/'mapped_geometry.json').write_text(json.dumps(geometry,indent=2));spec['output']=str(b/'mapped_base.tpac');spec['meshes'].append(dict(name=prefix+'_cloth_proxy',bodyPart='',template='mesh',groups=[{k:proxy[k] for k in ['name','geometry','material','flags','materialFlags']}]))
    (b/'mapped_spec.json').write_text(json.dumps(spec,indent=2));run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','build',b/'mapped_spec.json']);run(['dotnet',b/'package_patch/PackagePatch.dll',b/'mapped_base.tpac',b/'mapped_uncooked.tpac',b/'mapped_geometry.json',prefix,prefix+'_collision'])
    for name,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch'),('MappedClothPatch','mapped_patch')]:run(['dotnet','build',common/(name+'.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(b/(folder+'_obj'))+'/', '-o',b/folder])
    from driver_probe import prepare_driver_probe
    prepare_driver_probe(root)
    dump=b/'proxy_input';dump.mkdir(exist_ok=True);run(['dotnet',b/'cloth_probe/NativeClothProbe.dll',b/'mapped_uncooked.tpac',prefix+'_cloth_proxy','--dump-segments',dump]);paths=list(dump.glob('*.mesh.json'));assert len(paths)==1;mesh=json.loads(paths[0].read_text());assert np.max(abs(np.array(mesh['positions'])-p))<2e-6
    policy={'unanchored':'pin_upper','axis':2,'band_m':c['cloth_proxy_policy']['pin_band_m'],'min_vertices':2,'reason':'Highest surviving attachment edge of each independently rooted hair card/lock; small detached tips omitted from proxy and mapped to the continuous parent surface'}
    payload,plan=cook(mesh,policy);cooked=b/'proxy_cooked';cooked.mkdir(exist_ok=True);dest=cooked/(plan['guid']+'.bin');dest.write_bytes(payload);plan['path']=str(dest);(cooked/'manifest.json').write_text(json.dumps([plan],indent=2));run(['dotnet',b/'cloth_patch/ClothPatch.dll',b/'mapped_uncooked.tpac',cooked/'manifest.json',b/'proxy_ready.tpac','--allow-metameshes',prefix+'_cloth_proxy'])
    data=read(payload);sim=decode_positions(data);packed=data['rest_normals'];sn=np.column_stack([packed>>21,(packed>>10)&2047,packed&1023])/np.array([2047,2047,1023])*2-1;sn/=np.linalg.norm(sn,axis=1)[:,None];triangles=data['render_to_sim'][f];renderdump=b/'mapped_render_input';renderdump.mkdir(exist_ok=True);run(['dotnet',b/'cloth_probe/NativeClothProbe.dll',b/'mapped_uncooked.tpac',prefix+'_body','--dump-segments',renderdump]);maps=b/'render_maps';maps.mkdir(exist_ok=True);mapplans=[];reports=[]
    for path in sorted(renderdump.glob('*.mesh.json')):
        render=json.loads(path.read_text());rp=np.array(render['positions']);active=np.array(render['alpha'])>0;mi=np.zeros((len(rp),3),'u2');mw=np.zeros((len(rp),4),'f4');mw[:,0]=1;ids=np.flatnonzero(active)
        for chunk in np.array_split(ids,max(1,(len(ids)+599)//600)):
            ii,weights=project(rp[chunk],sim,sn,triangles);mi[chunk]=ii;mw[chunk]=weights
        err=np.linalg.norm(reconstruct(sim,sn,mi[active],mw[active])-rp[active],axis=1);assert err.max()<.001,(render['name'],float(err.max()));blob=write(mi,mw);dest=maps/(render['guid']+'.bin');dest.write_bytes(blob);mapplans.append(dict(guid=render['guid'],path=str(dest),sha256=hashlib.sha256(blob).hexdigest(),unmapped_vertices=[]));reports.append({'mesh':render['name'],'lod':render['lod'],'mapped_vertices':int(active.sum()),'rest_reconstruction_max_error_m':float(err.max()),'max_normal_offset_m':float(abs(mw[active,3]).max()),'max_barycentric_extrapolation':float(np.maximum(-mw[active,:3],0).max())})
    (maps/'manifest.json').write_text(json.dumps(mapplans,indent=2));native='D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/EmAssetPackages/armor555/armor555.tpac';run(['dotnet',b/'mapped_patch/MappedClothPatch.dll',b/'proxy_ready.tpac',root/'module'/c['id']/'AssetPackages'/(prefix+'.tpac'),maps/'manifest.json',prefix+'_body',prefix+'_cloth_proxy',native,'--native-driver-role']);(b/'proxy_source.json').write_text(json.dumps(mesh));(root/'reports/mapped_cloth.json').write_text(json.dumps({'proxy':plan,'render_maps':reports,'scope':'Selected long hair and attached hair ties only; all skirts/clothes remain skinned','game_verified':False},indent=2));print('HAIR_CLOTH_READY',c['id'],len(p),'proxy vertices',len(mapplans),'render maps',flush=True)

if __name__=='__main__':
    import sys
    build_cloth(Path(sys.argv[1]).resolve())
