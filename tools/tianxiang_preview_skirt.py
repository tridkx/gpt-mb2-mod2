"""Surface-based preview skirt diagnosis and local horizontal clearance.

Uses the model's own legs, original shape, native UI cycle and captured game
bone frames. Preserves body geometry, skirt height and all binding weights.
"""
from pathlib import Path
import sys,json
import numpy as np

def setup(R):
    W=next(p for p in R.parents if (p/'tools/asset_helpers').is_dir())
    sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
    from baker.skeleton import parse_skeljson
    from baker.animation import parse_animjson,skin_matrices
    cfg=json.loads((R/'tools/model_config.json').read_text())
    rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
    inv=np.linalg.inv(rig['restWorld']);poses=[]
    for i,row in enumerate(json.loads((R/'reports/captured_ui_poses_v0.1.0.json').read_text())):
        record=row['record'];world=np.array([b['posed_entity'] for b in record['bones']]).reshape(28,4,4).transpose(0,2,1)
        poses.append((f'captured_{i}',world@inv))
    anim=parse_animjson(json.loads((R/'reports/ui_neutral_female.json').read_text()))
    for frame in sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,32).astype(int))):
        poses.append((f'ui_cycle_{frame}',skin_matrices(rig,anim,int(frame))))
    manifest=json.loads((R/'build/manifest.json').read_text())
    source_to_part={m['source_object']:m['object'] for m in manifest}
    legs=[source_to_part[n] for n in cfg['legs_sources']]
    return cfg,poses,manifest,legs

def quantize(w):
    # Blender stores group weights as float32; emulate the actual exporter.
    w=w.astype('f4').astype('f8')
    ids=np.argsort(-w,axis=1)[:,:4];v=np.take_along_axis(w,ids,axis=1);v/=v.sum(1,keepdims=True)
    q=np.floor(v*255).astype(int);q[np.arange(len(q)),v.argmax(1)]+=255-q.sum(1)
    dense=np.zeros_like(w);np.put_along_axis(dense,ids,q/255,axis=1)
    return dense

def skin(p,w,mat):
    return sum(w[:,i,None]*(p@mat[i,:3,:3].T+mat[i,:3,3]) for i in np.flatnonzero(w.sum(0)))

def make_trees(arrays,legs,poses):
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    trees=[]
    for label,mat in poses:
        vertices=[];triangles=[]
        for part in legs:
            weights=arrays[part+'_w'] if arrays.get('_byte_weights',False) else quantize(arrays[part+'_w'])
            p=skin(arrays[part+'_p'],weights,mat);f=arrays[part+'_f']
            triangles.extend((f+len(vertices)).tolist());vertices.extend(p.tolist())
        trees.append((label,mat,BVHTree.FromPolygons([Vector(p) for p in vertices],triangles,all_triangles=True)))
    return trees

def score(p,w,f,trees,density=2,weights_quantized=False):
    from mathutils import Vector
    bary=np.array([[i,j,density-i-j] for i in range(density+1) for j in range(density+1-i)])/density
    tri=f[(p[f][:,:,2].mean(1)<.84)&(p[f][:,:,2].mean(1)>.06)]
    rest=np.einsum('bq,tqc->tbc',bary,p[tri]).reshape(-1,3)
    weights=w if weights_quantized else quantize(w)
    rows=[];maximum=0;total=0
    for label,mat,tree in trees:
        posed=skin(p,weights,mat)
        points=np.einsum('bq,tqc->tbc',bary,posed[tri]).reshape(-1,3)
        depth=[];worst_rest=None;worst_depth=0
        for qi,q in enumerate(points):
            hit,normal,index,distance=tree.find_nearest(Vector(q))
            if hit is not None and distance<.08:
                d=float((Vector(q)-hit).dot(normal))
                # Nearest points on an open skin/boot boundary do not define
                # a solid interior. Count only face-interior normal distances.
                if d<-.001 and -d/max(distance,1e-10)>.95:
                    depth.append(-d)
                    if -d>worst_depth:worst_depth=-d;worst_rest=rest[qi].tolist()
        maximum=max(maximum,max(depth,default=0));total+=len(depth)
        rows.append(dict(pose=label,penetrating_samples=len(depth),maximum_penetration_m=max(depth,default=0),worst_source_sample=worst_rest))
    return dict(maximum_penetration_m=maximum,penetrating_samples=total,poses=rows,samples_per_pose=len(rest))

def sculpt(R):
    import bpy
    from mathutils import Vector
    cfg,poses,manifest,legs=setup(R)
    fresh='fresh' in sys.argv;continuing='continue' in sys.argv
    base=np.load(R/'build'/('fitted_model.npz' if fresh or continuing else 'skirt_baseline.npz'));arrays={k:base[k].copy() for k in base.files}
    trees=make_trees(arrays,legs,poses);name=cfg['skirt_object']
    p=arrays[name+'_p'].copy();original=np.load(R/'build/skirt_baseline.npz')[name+'_p'] if continuing else p.copy();w=arrays[name+'_w'];f=arrays[name+'_f']
    other={tuple(np.round(v,5)) for m in manifest if m['object']!=name for v in arrays[m['object']+'_p']}
    fixed=np.array([tuple(np.round(v,5)) in other or v[2]>.85 for v in p])
    tri=f[(p[f][:,:,2].mean(1)<.84)&(p[f][:,:,2].mean(1)>.06)]
    bary=np.array([[i,j,4-i-j] for i in range(5) for j in range(5-i)])/4
    ids=np.repeat(tri,len(bary),axis=0);b=np.tile(bary,(len(tri),1))
    before=score(p,w,f,trees,density=4);logs=[]
    if continuing:before=score(original,w,f,trees,density=4)
    offsets_file=R/'tools/preview_skirt_offsets.npz'
    stored=fresh and offsets_file.exists()
    if stored:
        saved=np.load(offsets_file)
        assert saved['original_positions'].shape==original.shape and np.max(abs(saved['original_positions']-original))<1e-6
        assert (saved['offsets'][:,2]==0).all()
        p=original+saved['offsets']
    unique,owner=np.unique(np.round(original,5),axis=0,return_inverse=True)
    edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
    for iteration in range(0 if stored else 80):
        total=np.zeros_like(p);counts=np.zeros(len(p));violations=0;maximum=0
        for label,mat,tree in trees:
            posed=skin(p,quantize(w),mat)
            samples=(posed[ids]*b[:,:,None]).sum(1)
            A=np.einsum('vk,kij->vij',quantize(w),mat[:,:3,:3])
            for si,q in enumerate(samples):
                hit,n,index,distance=tree.find_nearest(Vector(q))
                if hit is None or distance>.08:continue
                normal=np.array(n);d=float((Vector(q)-hit).dot(n))
                if d>=.002 or abs(d)/max(distance,1e-10)<.95:continue
                v=ids[si];jac=np.einsum('vji,j->vi',A[v],normal);jac[:,2]=0;jac[fixed[v]]=0
                jac*=b[si,:,None];den=float((jac*jac).sum())
                if den<1e-9:continue
                delta=jac*(.002-d)/den
                np.add.at(total,v,delta);np.add.at(counts,v,1)
                violations+=int(d<-.001);maximum=max(maximum,-d)
        logs.append(dict(iteration=iteration,penetrating_samples=violations,maximum_depth_m=maximum))
        if violations==0:break
        update=total/np.maximum(counts[:,None],1);length=np.linalg.norm(update,axis=1)
        update*=np.minimum(1,.003/np.maximum(length,1e-10))[:,None]
        p+=update*.85
        # Smooth the displacement field, not the garment shape.
        displacement=p-original;neighbors=np.zeros_like(p);degree=np.zeros(len(p))
        np.add.at(neighbors,edges[:,0],displacement[edges[:,1]]);np.add.at(neighbors,edges[:,1],displacement[edges[:,0]])
        np.add.at(degree,edges[:,0],1);np.add.at(degree,edges[:,1],1)
        smoothing=.10 if iteration<20 and not continuing else .005
        smooth=displacement*(1-smoothing)+neighbors/np.maximum(degree[:,None],1)*smoothing
        averaged=np.zeros((len(unique),3));np.add.at(averaged,owner,smooth);averaged/=np.bincount(owner)[:,None]
        smooth=averaged[owner];smooth[fixed]=0;smooth[:,2]=0;p=original+smooth
        assert np.linalg.norm(p-original,axis=1).max()<.06,'Local correction exceeded 60mm'
        print('SCULPT_ITER',R.name,iteration,violations,maximum,flush=True)
    after=score(p,w,f,trees,density=4)
    assert after['penetrating_samples']<before['penetrating_samples']
    arrays[name+'_p']=p
    bpy.ops.wm.open_mainfile(filepath=str(R/'source'/(R.name+'_Rigged.blend') if fresh or continuing else R/'build/skirt_baseline.blend'))
    ob=bpy.data.objects[name];ob.data.vertices.foreach_set('co',p.astype('f4').ravel());ob.data.update()
    np.savez_compressed(R/'build/fitted_model.npz',**arrays)
    bpy.ops.wm.save_as_mainfile(filepath=str(R/'source'/(R.name+'_Rigged.blend')))
    bpy.ops.export_scene.fbx(filepath=str(R/'source'/(R.name+'_Rigged.fbx')),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
    report=dict(scope='Local horizontal skirt clearance; original body, skeleton, source height and all weights unchanged; no cloth solver',parts=[dict(part=name,before=before,after=after,maximum_offset_m=float(np.linalg.norm(p-original,axis=1).max()),changed_vertices=int((np.linalg.norm(p-original,axis=1)>1e-6).sum()))],iterations=logs)
    (R/'reports/preview_skirt_fit.json').write_text(json.dumps(report,indent=2))
    transfer=json.loads((R/'reports/weight_transfer.json').read_text())
    transfer.update(source_geometry_max_error_m=report['parts'][0]['maximum_offset_m'],source_body_geometry_max_error_m=0,
        local_skirt_clearance=report['parts'][0]['maximum_offset_m'],source_height_unchanged=True,all_binding_weights_unchanged=True)
    (R/'reports/weight_transfer.json').write_text(json.dumps(transfer,indent=2))
    print('SCULPT_RESULT',R.name,after['penetrating_samples'],after['maximum_penetration_m'],report['parts'][0]['maximum_offset_m'])

def verify(R):
    cfg,poses,manifest,legs=setup(R)
    W=next(p for p in R.parents if (p/'tools/asset_helpers').is_dir());sys.path.insert(0,str(W/'tools/asset_helpers/tools'))
    from georead import read_geo
    import hashlib
    package=R/'module'/R.name/'AssetPackages'/(cfg['race']+'.tpac')
    rows=[]
    fit_report=json.loads((R/'reports/preview_skirt_fit.json').read_text())
    targets={rec['part'] for rec in fit_report['parts']}
    for lod in range(4):
        grouped={}
        for file in (R/f'build/final_export_lod{lod}/geo').glob('*.bin'):
            for g in read_geo(file):
                name=g['name'].split('.lod')[0].split('.b')[0]
                if name not in targets and name not in legs:continue
                grouped.setdefault(name,[]).append(g)
        arrays={'_byte_weights':True}
        for name,meshes in grouped.items():
            ps=[];ws=[];fs=[];offset=0
            for g in meshes:
                w=np.zeros((len(g['pos']),28));np.add.at(w,(np.arange(len(w))[:,None],g['bi']),g['bw']/255.)
                ps.append(g['pos']);ws.append(w);fs.append(g['idx'].reshape(-1,3)+offset);offset+=len(w)
            arrays[name+'_p']=np.concatenate(ps);arrays[name+'_w']=np.concatenate(ws);arrays[name+'_f']=np.concatenate(fs)
        trees=make_trees(arrays,legs,poses)
        for name in targets:
            result=score(arrays[name+'_p'],arrays[name+'_w'],arrays[name+'_f'],trees,density=4,weights_quantized=True)
            rows.append(dict(lod=lod,part=name,**result))
    result=dict(status='pass' if all(row['penetrating_samples']==0 for row in rows) else 'fail',version=cfg['version'],
        final_package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),threshold_m=.001,
        scope='Final TPAC byte weights and actual leg/skirt triangles, all four LODs; 15 barycentric samples per skirt triangle, captured UI bone frames and 32 samples over preview idle cycle; open boundary edge contacts excluded; no cloth solver or game retest',
        game_verified=False,rows=rows)
    (R/'reports/preview_skirt_validation.json').write_text(json.dumps(result,indent=2))
    print('FINAL_PREVIEW_SKIRT_CHECK',R.name,result['status'],[(row['lod'],row['penetrating_samples'],row['maximum_penetration_m']) for row in rows],flush=True)
    assert result['status']=='pass'

if __name__=='__main__':
    (verify if 'verify' in sys.argv else sculpt)(Path(sys.argv[-1]).resolve())

