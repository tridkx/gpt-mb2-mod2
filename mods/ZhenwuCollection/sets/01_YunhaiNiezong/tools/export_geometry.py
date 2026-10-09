"""Export Mingyu LODs, retaining all shared skin attachments exactly."""
import bpy,json,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/pipeline'))
from build_assets import vertex_tangents
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/ZhenwuYunhai_Rigged.blend'))
manifest=json.loads((ROOT/'build/rig_manifest.json').read_text());cfg=json.loads((ROOT/'tools/model_config.json').read_text())
(ROOT/'build/mesh').mkdir(exist_ok=True)
owners={}
for r in manifest:
    for v in bpy.data.objects[r['object']].data.vertices:owners.setdefault(tuple(round(c,5) for c in v.co),set()).add(r['object'])
shared={p for p,names in owners.items() if len(names)>1}
groups=[]
veil_plan={'panels':[]}
for r in manifest:
    original=bpy.data.objects[r['object']]
    seam_normals={tuple(round(c,5) for c in original.data.vertices[loop.vertex_index].co):original.data.corner_normals[loop.index].vector.copy() for loop in original.data.loops if tuple(round(c,5) for c in original.data.vertices[loop.vertex_index].co) in shared} if r['texture_key'] in ['skin','face'] else {}
    saved={tuple(round(c,5) for c in v.co):[(original.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in original.data.vertices if tuple(round(c,5) for c in v.co) in shared}
    # Keep the full face in all LODs: a small mesh whose cuts define the neck.
    for lod,ratio in enumerate(cfg['lod_ratios']):
        saved_lod=dict(saved)
        if lod==1 and r['kind']=='upper_clothes':
            for panel in veil_plan['panels']:
                for vi in panel['fixed_vertices']:
                    v=original.data.vertices[vi]
                    saved_lod[tuple(round(c,5) for c in v.co)]=[(original.vertex_groups[g.group].name,g.weight) for g in v.groups]
        o=original.copy();o.data=original.data.copy();bpy.context.scene.collection.objects.link(o)
        for mod in list(o.modifiers):o.modifiers.remove(mod)
        bpy.context.view_layer.objects.active=o;fallback=False
        if lod and r['texture_key'] not in ['face','eye','lash']:
            guard=o.vertex_groups.new(name='SeamGuard')
            ids=[v.index for v in o.data.vertices if tuple(round(c,5) for c in v.co) in saved_lod]
            if ids:guard.add(ids,1,'REPLACE')
            dec=o.modifiers.new('LOD','DECIMATE');dec.ratio=ratio
            dec.vertex_group=guard.name;dec.vertex_group_factor=1000;dec.invert_vertex_group=True
            bpy.ops.object.modifier_apply(modifier=dec.name)
            coords={tuple(round(c,5) for c in v.co) for v in o.data.vertices}
            if not set(saved_lod).issubset(coords):o.data=original.data.copy();fallback=True
            guard=o.vertex_groups.get('SeamGuard')
            if guard:o.vertex_groups.remove(guard)
            for v in o.data.vertices:
                ws=saved_lod.get(tuple(round(c,5) for c in v.co))
                if ws is not None:
                    for group in o.vertex_groups:group.remove([v.index])
                    for name,weight in ws:o.vertex_groups[name].add([v.index],weight,'REPLACE')
        me=o.data
        if seam_normals:
            normals=[seam_normals.get(tuple(round(c,5) for c in me.vertices[loop.vertex_index].co),me.corner_normals[loop.index].vector.copy()) for loop in me.loops]
            me.normals_split_custom_set(normals)
        me.calc_loop_triangles();uv=me.uv_layers.active.data;alpha=me.color_attributes.get('ClothDistance')
        records=[];faces=[];dedup={}
        for tri in me.loop_triangles:
            face=[]
            for li in tri.loops:
                vi=me.loops[li].vertex_index;v=me.vertices[vi];n=me.corner_normals[li].vector.copy()
                if n.length<1e-8:n=tri.normal.copy()
                if n.length<1e-8:n[:]=(0,0,1)
                n.normalize();u=list(uv[li].uv);u[1]=1-u[1]
                key=(vi,tuple(round(x,6) for x in n),tuple(round(x,7) for x in u))
                if key not in dedup:
                    inf=sorted([(int(o.vertex_groups[g.group].name.rsplit('_',1)[1]),g.weight) for g in v.groups if g.weight>1e-6],key=lambda x:-x[1])[:4]
                    assert inf
                    idx=[i for i,w in inf];w=np.array([w for i,w in inf]);w/=w.sum()
                    q=np.floor(w*255).astype(int);q[w.argmax()]+=255-q.sum()
                    while len(idx)<4:idx.append(0);q=np.append(q,0)
                    cloth_lod=lod in cfg.get('cloth_lods',{}).get(r['kind'],[0])
                    a=alpha.data[vi].color[3] if alpha and cloth_lod else 0
                    records.append((list(v.co),list(n),u,idx,q.tolist(),[255,255,255,round(a*255)]));dedup[key]=len(records)-1
                face.append(dedup[key])
            faces.append(face)
        p=np.array([v[0] for v in records]);n=np.array([v[1] for v in records]);uvs=np.array([v[2] for v in records]);f=np.array(faces)
        tangent=vertex_tangents(p,f,uvs,n);assert np.isfinite(tangent).all()
        name=r['object']+('' if lod==0 else '.lod'+str(lod));path=ROOT/'build/mesh'/(name+'.mgeo')
        with path.open('wb') as out:
            out.write(np.array([0x4f45474d,len(p),f.size],'<i4').tobytes())
            for a in [p,n,tangent,uvs,np.zeros((len(p),2))]:out.write(np.asarray(a,'<f4').tobytes())
            for a in [[v[5] for v in records],[v[3] for v in records],[v[4] for v in records]]:out.write(np.asarray(a,'u1').tobytes())
            out.write(f.astype('<u4').tobytes())
        groups.append({'part':r['part'],'kind':r['kind'],'name':name,'geometry':str(path),'material':r['material'],'flags':[],'materialFlags':['no_team_color','no_tattoo'],'lod':lod,'vertices':len(p),'tris':len(f),'cloth':r['cloth'] and cloth_lod,'boundary_fallback':fallback})
        bpy.data.objects.remove(o,do_unlink=True)
(ROOT/'build/geometry.json').write_text(json.dumps(groups,indent=2))
stats=[{'lod':i,'triangles':sum(g['tris'] for g in groups if g['lod']==i),'fallbacks':[g['name'] for g in groups if g['lod']==i and g['boundary_fallback']]} for i in range(4)]
(ROOT/'reports/lod_stats.json').write_text(json.dumps(stats,indent=2));print('GEOMETRY_READY',stats)
