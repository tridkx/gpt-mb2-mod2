"""Patch clothing surface openings left by Tripo's fused hair segmentation."""
import bmesh
import numpy as np
from collections import Counter,defaultdict
from mathutils import Vector
def repair(objects):
    hair=next(o for o in objects if o.name=='tripo_part_0')
    hair_points={tuple(round(c,5) for c in hair.matrix_world@v.co) for v in hair.data.vertices}
    image=next(n.image for n in hair.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    pixels=np.empty(len(image.pixels),dtype='f4');image.pixels.foreach_get(pixels);pixels=pixels.reshape(image.size[1],image.size[0],4)
    records=[]
    for o in objects:
        part=int(o.name.rsplit('_',1)[1])
        if part not in {18,29}:continue
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
            contact=[tuple(round(c,5) for c in o.matrix_world@o.data.vertices[i].co) in hair_points for i in loop]
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
        uv_lookup={v.index:next((l[uv].uv.copy() for f in v.link_faces for l in f.loops if l.vert==v),Vector((0,0))) for v in bm.verts}
        # Newly exposed areas have no original clothing texture (they were
        # hair). Use a matching blue atlas sample rather than interpolating
        # across unrelated UV islands and creating red streaks.
        candidates=list(uv_lookup.values())
        color=np.array([pixels[int(np.clip(u.y*image.size[1],0,image.size[1]-1)),int(np.clip(u.x*image.size[0],0,image.size[0]-1)),:3] for u in candidates])
        patch_uv=candidates[int(np.argmin(np.sum((color-[.48,.62,.75])**2,axis=1)))]
        added=0
        for chain in patches:
            if len(set(chain))<3:continue
            try:face=bm.faces.new([bm.verts[i] for i in chain])
            except ValueError:continue
            face.normal_update();adjacent=Vector()
            for v in face.verts:
                for f in v.link_faces:
                    if f!=face:adjacent+=f.normal
            if face.normal.dot(adjacent)<0:face.normal_flip()
            for l in face.loops:l[uv].uv=patch_uv
            result=bmesh.ops.triangulate(bm,faces=[face],quad_method='BEAUTY',ngon_method='BEAUTY');added+=len(result['faces'])
        bm.to_mesh(o.data);bm.free();o.data.update()
        records.append({'source_part':part,'patches':len(patches),'added_triangles':added})
    return records
