"""Patch clothing surface openings left by Tripo's fused hair segmentation."""
import bmesh
import numpy as np
from collections import Counter,defaultdict
from mathutils import Vector
from mathutils.kdtree import KDTree
def repair(objects):
    hair=next(o for o in objects if o.name=='tripo_part_0')
    hair_points={tuple(round(c,5) for c in hair.matrix_world@v.co) for v in hair.data.vertices}
    image=next(n.image for n in hair.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    pixels=np.empty(len(image.pixels),dtype='f4');image.pixels.foreach_get(pixels);pixels=pixels.reshape(image.size[1],image.size[0],4)
    records=[]
    for o in objects:
        part=int(o.name.rsplit('_',1)[1])
        if part not in {18,29}:continue
        # Remove only the rear garment's dark hair remnants. Sample the restored
        # atlas at corners and centroid; blue textile has a much higher blue
        # channel than these nearly neutral black strands.
        bm=bmesh.new();bm.from_mesh(o.data);uv=bm.loops.layers.uv.active
        remove=[]
        for f in bm.faces:
            center=o.matrix_world@f.calc_center_median()
            coords=[l[uv].uv.copy() for l in f.loops]
            coords.append(sum(coords,Vector((0,0)))/len(coords))
            colors=np.array([pixels[int(np.clip(u.y*image.size[1],0,image.size[1]-1)),int(np.clip(u.x*image.size[0],0,image.size[0]-1)),:3] for u in coords])
            c=colors.mean(0)
            if center.x<-.012 and c.max()<.34 and c.max()-c.min()<.12:remove.append(f)
        removed=len(remove)
        # Include the immediate jagged fringe, which mixes black hair pixels
        # with blue cloth and would otherwise leave numerous tiny slit loops.
        remove=set(remove)
        fringe={ff for f in remove for e in f.edges for ff in e.link_faces if (o.matrix_world@ff.calc_center_median()).x<-.012}
        remove=list(remove|fringe)
        removed=len(remove)
        cut_points={tuple(round(c,5) for c in o.matrix_world@v.co) for f in remove for v in f.verts}
        bmesh.ops.delete(bm,geom=remove,context='FACES')
        bm.to_mesh(o.data);bm.free();o.data.update()
        ec=Counter(e for f in o.data.polygons for e in f.edge_keys);adj=defaultdict(set)
        for e,count in ec.items():
            if count==1:adj[e[0]].add(e[1]);adj[e[1]].add(e[0])
        seen=set();patches=[]
        for start in adj:
            if start in seen:continue
            if len(adj[start])!=2:continue
            loop=[start];previous=None;current=start
            while True:
                options=adj[current]-({previous} if previous is not None else set())
                nxt=next(iter(options))
                if nxt==start:break
                if nxt in loop:break
                loop.append(nxt);previous,current=current,nxt
            seen.update(loop)
            points=[o.matrix_world@o.data.vertices[i].co for i in loop]
            # These are model-local back openings. Do not split the long rear
            # contour into UV/color-dependent runs: bridge all rear points of
            # the torso opening, and only the upper waist hole on the panel.
            contact=[(p.x<-.012 and abs(p.y)<(.085 if part==29 else .07) and ((.60<p.z<.90) if part==29 else (.51<p.z<.62))) for p in points]
            if sum(contact)<3:continue
            if sum(contact)/len(loop)>.7:
                patches.append(loop)
            else:
                # Close each hair contact indentation with a chord, retaining
                # the adjacent collar, waist and sleeve opening.
                noncontact=next(i for i,v in enumerate(contact) if not v)
                ordered=loop[noncontact:]+loop[:noncontact];marks=contact[noncontact:]+contact[:noncontact]
                i=1
                while i<len(ordered):
                    if not marks[i]:i+=1;continue
                    first=i
                    while i<len(ordered) and marks[i]:i+=1
                    if i-first>=3:
                        chain=ordered[first-1:min(i+1,len(ordered))]
                        if i==len(ordered):chain.append(ordered[0])
                        patches.append(chain)
        bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();uv=bm.loops.layers.uv.active
        original_vertices=list(bm.verts)
        uv_lookup={v.index:next((l[uv].uv.copy() for f in v.link_faces for l in f.loops if l.vert==v),Vector((0,0))) for v in bm.verts}
        # Newly exposed areas have no original clothing texture (they were
        # hair). Use a matching blue atlas sample rather than interpolating
        # across unrelated UV islands and creating red streaks.
        candidates=list(uv_lookup.values())
        color=np.array([pixels[int(np.clip(u.y*image.size[1],0,image.size[1]-1)),int(np.clip(u.x*image.size[0],0,image.size[0]-1)),:3] for u in candidates])
        patch_uv=candidates[int(np.argmin(np.sum((color-[.48,.62,.75])**2,axis=1)))]
        added=0;patch_records=[];all_patch_faces=[]
        for chain in patches:
            if len(set(chain))<3:continue
            try:face=bm.faces.new([original_vertices[i] for i in chain])
            except ValueError:continue
            face.normal_update();adjacent=Vector()
            for v in face.verts:
                for f in v.link_faces:
                    if f!=face:adjacent+=f.normal
            if face.normal.dot(adjacent)<0:face.normal_flip()
            for l in face.loops:l[uv].uv=patch_uv
            result=bmesh.ops.triangulate(bm,faces=[face],quad_method='BEAUTY',ngon_method='BEAUTY')
            patch_faces=result['faces']
            all_patch_faces.extend(patch_faces)
            patch_records.append({'boundary_vertices':len(chain)})
            added+=len(patch_faces)
        patch_set=set(f for f in all_patch_faces if f.is_valid)
        fixed=set(v for f in patch_set for v in f.verts)
        edges=list(set(e for f in patch_set for e in f.edges if len(e.link_faces)==2 and all(ff in patch_set for ff in e.link_faces)))
        existing={tuple(round(c,7) for c in v.co) for v in bm.verts}
        rear_boundary=[o.matrix_world@v.co for v in fixed if (o.matrix_world@v.co).x<-.012]
        guard=KDTree(len(rear_boundary))
        for i,p in enumerate(rear_boundary):guard.insert(Vector((p.y,p.z,0)),i)
        guard.balance()
        result=bmesh.ops.subdivide_edges(bm,edges=edges,cuts=5,use_grid_fill=True)
        interior=[v for v in bm.verts if tuple(round(c,7) for c in v.co) not in existing]
        for _ in range(80):
            new=[sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges) for v in interior]
            for v,co in zip(interior,new):v.co=v.co.lerp(co,.6)
        # AI hair borders curl into the hollow garment. Extend the missing
        # rear cloth along its exterior depth, rather than their inward chord.
        for v in interior:
            p=o.matrix_world@v.co
            if not (abs(p.y)<(.075 if part==29 else .045) and ((.61<p.z<.835) if part==29 else (.53<p.z<.59))):continue
            rear_depth=(-.070+.7*p.y**2) if part==29 else (-.085+.8*p.y**2)
            distance=guard.find(Vector((p.y,p.z,0)))[2]
            blend=min(1,distance/.015)
            blend=blend*blend*(3-2*blend)
            if part==29:blend*=min(1,max(0,(.835-p.z)/.025))
            p.x+=blend*(min(p.x,rear_depth)-p.x)
            v.co=o.matrix_world.inverted()@p
        for v in interior:
            for l in v.link_loops:l[uv].uv=patch_uv
        bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
        # Degenerate triangles and duplicate corner vertices left by the AI
        # border can leave pinholes after triangulation. Weld only coincident
        # points, then close residual local rear loops without touching hems.
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
        remaining=[]
        for e in bm.edges:
            if not e.is_boundary:continue
            points=[o.matrix_world@v.co for v in e.verts]
            if all(p.x<-.012 and abs(p.y)<.085 and ((.60<p.z<.80) if part==29 else (.51<p.z<.625)) for p in points):remaining.append(e)
        filled=bmesh.ops.holes_fill(bm,edges=remaining,sides=0)['faces']
        for f in filled:
            for l in f.loops:l[uv].uv=patch_uv
        bmesh.ops.triangulate(bm,faces=list(filled),quad_method='BEAUTY',ngon_method='BEAUTY')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(o.data);bm.free();o.data.update()
        records.append({'source_part':part,'patches':len(patches),'initial_patch_triangles':added,'removed_black_hair_faces':removed,'patch_details':patch_records,'closed_residual_loops':len(filled)})
    return records
