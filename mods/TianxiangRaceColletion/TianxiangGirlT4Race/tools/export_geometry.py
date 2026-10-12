import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
"""Export protected material/cut boundaries, native byte weights and four LODs."""
import bpy,json,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORKSPACE=workspace_root(ROOT)
sys.path.insert(0,str(WORKSPACE/'tools/asset_helpers/pipeline'))
from build_assets import vertex_tangents
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangGirlT4Race_Rigged.blend'))
manifest=json.loads((ROOT/'build/manifest.json').read_text());(ROOT/'build/mesh').mkdir(exist_ok=True)
cfg=json.loads((ROOT/'tools/model_config.json').read_text());geometry=[];stats=[]
shared={}
for rec in manifest:
    if rec['kind']=='hair':continue
    for v in bpy.data.objects[rec['object']].data.vertices:
        shared.setdefault(tuple(np.round(v.co,5)),set()).add(rec['object'])
shared={p for p,owners in shared.items() if len(owners)>1}
for rec in manifest:
    original=bpy.data.objects[rec['object']]
    # Source vertices split at UV/normal seams. Weld geometric vertices before
    # simplification while retaining UVs on face loops; otherwise almost every
    # atlas split would be incorrectly protected as an equipment boundary.
    bpy.ops.object.select_all(action='DESELECT');original.select_set(True)
    bpy.context.view_layer.objects.active=original
    # Preserve source attachment islands: overlapping ornament vertices must not
    # become fixed roots of an unrelated hanging cloth panel.
    import bmesh
    bm=bmesh.new();bm.from_mesh(original.data);remaining=set(bm.verts)
    while remaining:
        seed=remaining.pop();island={seed};pending=[seed]
        while pending:
            v=pending.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in remaining:remaining.remove(other);island.add(other);pending.append(other)
        bmesh.ops.remove_doubles(bm,verts=list(island),dist=.000001)
    bm.to_mesh(original.data);bm.free();original.data.update()
    edge_faces={}
    for f in original.data.polygons:
        for edge in f.edge_keys:edge_faces[edge]=edge_faces.get(edge,0)+1
    boundary={v for edge,count in edge_faces.items() if count==1 for v in edge}
    # Hair strands, eyebrows and lashes have many intentional free edges.
    # They are not equipment attachment cuts and should simplify at distance.
    if rec['kind']=='hair' or 'Eyelash' in rec['material'] or rec['material']=='eyelash_new_Inst':boundary=set()
    boundary.update(v.index for v in original.data.vertices if tuple(np.round(v.co,5)) in shared)
    points={tuple(np.round(original.data.vertices[i].co,6)) for i in boundary}
    saved={tuple(np.round(original.data.vertices[i].co,6)):[(original.vertex_groups[g.group].name,g.weight) for g in original.data.vertices[i].groups] for i in boundary}
    base=1.0
    # Small geometric lash strips remain stable in the source; boundaries guard attachments.
    if rec['material']=='eyelash_new_Inst':base=1
    for lod,mult in enumerate(cfg['lod_multipliers']):
        o=original.copy();o.data=original.data.copy();bpy.context.collection.objects.link(o)
        for m in list(o.modifiers):o.modifiers.remove(m)
        bpy.context.view_layer.objects.active=o
        guard=o.vertex_groups.new(name='boundary_guard')
        if boundary:guard.add(list(boundary),1,'REPLACE')
        dec=o.modifiers.new('LOD','DECIMATE');dec.ratio=max(base*mult,cfg['minimum_ratios'].get(rec['material'],0));dec.vertex_group=guard.name;dec.vertex_group_factor=1000;dec.invert_vertex_group=True
        bpy.ops.object.modifier_apply(modifier=dec.name)
        fallback=not points.issubset({tuple(np.round(v.co,6)) for v in o.data.vertices})
        if fallback:o.data=original.data.copy()
        if o.vertex_groups.get('boundary_guard'):o.vertex_groups.remove(o.vertex_groups['boundary_guard'])
        for v in o.data.vertices:
            key=tuple(np.round(v.co,6))
            if key not in saved:continue
            for g in o.vertex_groups:g.remove([v.index])
            for name,w in saved[key]:o.vertex_groups[name].add([v.index],w,'REPLACE')
        me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;cloth_layer=me.color_attributes.get("ClothDistance");records=[];faces=[];dedup={}
        for tri in me.loop_triangles:
            if tri.area<1e-12:continue
            face=[]
            for li in tri.loops:
                vi=me.loops[li].vertex_index;v=me.vertices[vi];normal=me.corner_normals[li].vector.copy()
                if normal.length<1e-8:normal=tri.normal.copy()
                if normal.length<1e-8:normal=v.normal.copy()
                if normal.length<1e-8:normal[:]=(0,0,1)
                normal.normalize()
                u=list(uv[li].uv);u[1]=1-u[1];key=(vi,tuple(round(x,6) for x in normal),tuple(round(x,7) for x in u))
                if key not in dedup:
                    inf=sorted([(int(o.vertex_groups[g.group].name.rsplit('_',1)[1]),g.weight) for g in v.groups if g.weight>1e-7],key=lambda x:-x[1])[:4]
                    idx=[i for i,w in inf];w=np.array([w for i,w in inf]);w/=w.sum();q=np.floor(w*255).astype(int);q[w.argmax()]+=255-q.sum()
                    while len(idx)<4:idx.append(0);q=np.append(q,0)
                    records.append((list(v.co),list(normal),u,idx,q.tolist(),cloth_layer.data[vi].color[3] if cloth_layer else 0));dedup[key]=len(records)-1
                face.append(dedup[key])
            faces.append(face)
        p=np.array([v[0] for v in records]);n=np.array([v[1] for v in records]);u=np.array([v[2] for v in records]);f=np.array(faces)
        tangent=vertex_tangents(p,f,u,n);name=rec['object']+('' if lod==0 else '.lod'+str(lod));path=ROOT/'build/mesh'/(name+'.mgeo')
        with path.open('wb') as out:
            out.write(np.array([0x4f45474d,len(p),f.size],'<i4').tobytes())
            for a in [p,n,tangent,u,np.zeros((len(p),2))]:out.write(np.asarray(a,'<f4').tobytes())
            color=np.full((len(p),4),255,'u1');active=cfg['cloth_enabled'] and any(v[5]>0 for v in records) and lod in cfg['cloth_lods']
            if active:color[:,3]=np.rint(np.clip([v[5] for v in records],0,1)*255).astype('u1')
            for a in [color,[v[3] for v in records],[v[4] for v in records]]:out.write(np.asarray(a,'u1').tobytes())
            out.write(f.astype('<u4').tobytes())
        assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(tangent).all()
        geometry.append({'name':name,'part':rec['part'],'geometry':str(path),'material':'txgirl4_'+rec['material'].lower(),'flags':[],'materialFlags':['no_team_color','no_tattoo'],'lod':lod,'vertices':len(p),'triangles':len(f),'boundary_fallback':fallback,'cloth':active})
        bpy.data.objects.remove(o,do_unlink=True)
# Tiny tetrahedron inside the pelvis supplies valid unused skin slots.
from build_assets import vertex_tangents
p=np.array([[0,0,.81],[.0001,0,.81],[0,.0001,.81],[0,0,.811]],dtype='f4');f=np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3]],dtype='u4')
n=np.tile([0,0,1],(4,1));u=np.zeros((4,2));tangent=vertex_tangents(p,f,u,n)
path=ROOT/'build/mesh/txgirl4_hidden.mgeo'
with path.open('wb') as out:
    out.write(np.array([0x4f45474d,4,12],'<i4').tobytes())
    for a in [p,n,tangent,u,u]:out.write(np.asarray(a,'<f4').tobytes())
    for a in [np.full((4,4),255,'u1'),np.zeros((4,4),'u1'),np.tile([255,0,0,0],(4,1))]:out.write(np.asarray(a,'u1').tobytes())
    out.write(f.astype('<u4').tobytes())
geometry.append(dict(name='txgirl4_hidden',part='hidden',geometry=str(path),material='txgirl4_body_d',flags=[],materialFlags=['no_team_color','no_tattoo'],lod=0,vertices=4,triangles=4,boundary_fallback=False))
(ROOT/'build/geometry.json').write_text(json.dumps(geometry,indent=2))
for lod in range(4):stats.append({'lod':lod,'triangles':sum(g['triangles'] for g in geometry if g['lod']==lod and g['part']!='hidden'),'vertices':sum(g['vertices'] for g in geometry if g['lod']==lod and g['part']!='hidden'),'boundary_fallbacks':[g['name'] for g in geometry if g['lod']==lod and g['boundary_fallback']]})
(ROOT/'reports/lod_stats.json').write_text(json.dumps(stats,indent=2));print('GEOMETRY_READY',stats)
