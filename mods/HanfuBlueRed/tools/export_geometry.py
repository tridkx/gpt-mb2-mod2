"""Export four Hanfu LODs with protected part cuts and quantized weights."""
import bpy,json,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'D:\gpt-mb2-mod\pipeline')
from build_assets import vertex_tangents
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/HanfuBlueRed_Rigged.blend'))
manifest=json.loads((ROOT/'build/rig_manifest.json').read_text())
only=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else None
(ROOT/'build/mesh').mkdir(exist_ok=True)
ratios={'hair':.22,'face_neck':1,'ornament':.5,'torso':.23,'sleeve':.22,'hand':.65,'panel':.18,'belt_tassel':.22,'pants':.14,'shoe':.30}
groups=[];lod_stats=[]
position_owners={}
for rec in manifest:
    for v in bpy.data.objects[rec['object']].data.vertices:
        position_owners.setdefault(tuple(round(c,5) for c in v.co),set()).add(rec['object'])
shared_positions={p for p,owners in position_owners.items() if len(owners)>1}
for rec in manifest:
    if only and rec['object']!=only:continue
    original=bpy.data.objects[rec['object']]
    edge_faces={}
    for f in original.data.polygons:
        for e in f.edge_keys:edge_faces[e]=edge_faces.get(e,0)+1
    boundary={v for e,count in edge_faces.items() if count==1 for v in e}
    boundary.update(v.index for v in original.data.vertices if tuple(round(c,5) for c in v.co) in shared_positions)
    boundary_points={tuple(round(c,5) for c in original.data.vertices[v].co) for v in boundary}
    boundary_weights={tuple(round(c,5) for c in original.data.vertices[v].co):[(original.vertex_groups[g.group].name,g.weight) for g in original.data.vertices[v].groups] for v in boundary}
    for lod,mult in [(0,1),(1,.48),(2,.20),(3,.075)]:
        o=original.copy();o.data=original.data.copy();bpy.context.scene.collection.objects.link(o)
        for m in list(o.modifiers):o.modifiers.remove(m)
        bpy.context.view_layer.objects.active=o
        ratio=ratios[rec['kind']]*mult
        fallback=False
        # Face and skin attachment boundaries are exact in every LOD.
        if ratio<1:
            guard=o.vertex_groups.new(name='LOD_cut_guard');guard.add(list(boundary),1,'REPLACE')
            dec=o.modifiers.new('LOD','DECIMATE');dec.ratio=ratio;dec.vertex_group=guard.name;dec.vertex_group_factor=1000;dec.invert_vertex_group=True
            bpy.ops.object.modifier_apply(modifier=dec.name)
            current={tuple(round(c,5) for c in v.co) for v in o.data.vertices}
            if not boundary_points.issubset(current):
                o.data=original.data.copy();fallback=True
            guard=o.vertex_groups.get('LOD_cut_guard')
            if guard:o.vertex_groups.remove(guard)
            # A pinned boundary can retain its coordinate while a collapse
            # interpolates its vertex groups. Restore its original influences.
            for v in o.data.vertices:
                saved=boundary_weights.get(tuple(round(c,5) for c in v.co))
                if saved is None:continue
                for group in o.vertex_groups:group.remove([v.index])
                for name,weight in saved:o.vertex_groups[name].add([v.index],weight,'REPLACE')
        me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
        alpha=me.color_attributes.get('ClothDistance');records=[];faces=[];dedup={}
        for tri in me.loop_triangles:
            face=[]
            for li in tri.loops:
                vi=me.loops[li].vertex_index;v=me.vertices[vi];n=me.corner_normals[li].vector.copy()
                if n.length<1e-8:n=tri.normal.copy()
                if n.length<1e-8:n=v.normal.copy()
                if n.length<1e-8:n[:]=(0,0,1)
                n.normalize()
                u=list(uv[li].uv);u[1]=1-u[1];key=(vi,tuple(round(x,6) for x in n),tuple(round(x,7) for x in u))
                if key not in dedup:
                    influence=sorted([(int(o.vertex_groups[g.group].name.rsplit('_',1)[1]),g.weight) for g in v.groups if g.weight>1e-6 and o.vertex_groups[g.group].name.rsplit('_',1)[-1].isdigit()],key=lambda x:-x[1])[:4]
                    idx=[i for i,w in influence];w=np.array([w for i,w in influence]);assert len(w)>0
                    w/=w.sum();q=np.floor(w*255).astype(int);q[w.argmax()]+=255-q.sum()
                    while len(idx)<4:idx.append(0);q=np.append(q,0)
                    a=alpha.data[vi].color[3] if alpha and lod==0 else 0
                    records.append((list(v.co),list(n),u,idx,q.tolist(),[255,255,255,round(a*255)]));dedup[key]=len(records)-1
                face.append(dedup[key])
            faces.append(face)
        p=np.array([v[0] for v in records]);n=np.array([v[1] for v in records]);uvs=np.array([v[2] for v in records]);f=np.array(faces)
        tangents=vertex_tangents(p,f,uvs,n);name=o.name.split('.')[0]+('' if lod==0 else '.lod'+str(lod))
        path=ROOT/'build/mesh'/(name+'.mgeo')
        with path.open('wb') as out:
            out.write(np.array([0x4f45474d,len(p),f.size],'<i4').tobytes())
            for a in [p,n,tangents,uvs,np.zeros((len(p),2))]:out.write(np.asarray(a,'<f4').tobytes())
            for a in [[v[5] for v in records],[v[3] for v in records],[v[4] for v in records]]:out.write(np.asarray(a,'u1').tobytes())
            out.write(f.astype('<u4').tobytes())
        assert np.isfinite(p).all() and np.isfinite(tangents).all()
        groups.append({'part':rec['part'],'kind':rec['kind'],'name':name,'geometry':str(path),'material':'hbr_cloth','flags':[],'materialFlags':['no_team_color','no_tattoo'],'lod':lod,'vertices':len(p),'tris':len(f),'cloth':rec['cloth'] and lod==0,'boundary_fallback':fallback})
        bpy.data.objects.remove(o,do_unlink=True)
if only:
    changed={g['name']:g for g in groups}
    groups=[changed.get(g['name'],g) for g in json.loads((ROOT/'build/geometry.json').read_text())]
(ROOT/'build/geometry.json').write_text(json.dumps(groups,indent=2))
for lod in range(4):lod_stats.append({'lod':lod,'triangles':sum(g['tris'] for g in groups if g['lod']==lod),'fallback_parts':[g['name'] for g in groups if g['lod']==lod and g['boundary_fallback']]})
(ROOT/'reports/lod_stats.json').write_text(json.dumps(lod_stats,indent=2))
print('GEOMETRY_READY',lod_stats)
