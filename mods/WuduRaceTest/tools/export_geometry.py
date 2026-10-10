"""Export unchanged source geometry with native byte skinning; no cloth/LOD fitting."""
import bpy,json,sys
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];WS=R.parents[1]
sys.path.insert(0,str(WS/'tools/asset_helpers/pipeline'))
from build_assets import vertex_tangents
cfg=json.loads((R/'tools/model_config.json').read_text());K=cfg['unit_scale']/.01
bpy.ops.wm.open_mainfile(filepath=str(R/'source/WuduCanglan_Rigged.blend'))
(R/'build/mesh').mkdir(exist_ok=True);rows=[]
def save(name,p,normal,uv,ids,weights,faces,material,part,lod,alpha):
    tangent=vertex_tangents(p,faces,uv,normal)
    assert np.isfinite(p).all() and np.isfinite(tangent).all()
    for once in [0]:
        meshname=name+('' if lod==0 else '.lod'+str(lod));path=R/'build/mesh'/(meshname+'.mgeo')
        with path.open('wb') as out:
            out.write(np.array([0x4f45474d,len(p),faces.size],'<i4').tobytes())
            for a in [p,normal,tangent,uv,np.zeros((len(p),2))]:out.write(np.asarray(a,'<f4').tobytes())
            color=np.full((len(p),4),255,'u1');color[:,3]=np.rint(np.clip(alpha,0,1)*255).astype('u1')
            for a in [color,ids,weights]:out.write(np.asarray(a,'u1').tobytes())
            out.write(faces.astype('<u4').tobytes())
        rows.append(dict(part=part,name=meshname,geometry=str(path),material=material,flags=[],materialFlags=['no_team_color','no_tattoo'],lod=lod,vertices=len(p),triangles=len(faces),cloth=bool(np.any(alpha>0))))
for row in json.loads((R/'build/rig_manifest.json').read_text()):
    original=bpy.data.objects[row['object']]
    for lod,ratio in enumerate(cfg['lod_ratios']):
        ob=original.copy();ob.data=original.data.copy();bpy.context.collection.objects.link(ob)
        ob.modifiers.clear();bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        if lod>0:
            mod=ob.modifiers.new('Distance reduction','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
            bpy.ops.object.modifier_apply(modifier=mod.name)
        me=ob.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;records=[];faces=[];dedup={}
        layer=me.color_attributes.get('ClothDistance')
        for tri in me.loop_triangles:
            face=[]
            for li in tri.loops:
                vi=me.loops[li].vertex_index;v=me.vertices[vi];normal=me.corner_normals[li].vector.normalized();u=list(uv[li].uv);u[1]=1-u[1];key=(vi,tuple(normal),tuple(u))
                if key not in dedup:
                    influences=sorted([(int(ob.vertex_groups[g.group].name.rsplit('_',1)[1]),g.weight) for g in v.groups if g.weight>0],key=lambda x:-x[1])[:4]
                    ids=[i for i,w in influences];w=np.array([w for i,w in influences]);w/=w.sum();q=np.rint(w*255).astype(int);q[w.argmax()]+=255-q.sum()
                    while len(ids)<4:ids.append(0);q=np.append(q,0)
                    a=layer.data[vi].color[3] if layer and lod in cfg['cloth_lods'] else 0
                    dedup[key]=len(records);records.append((list(v.co),list(normal),u,ids,q.tolist(),a))
                face.append(dedup[key])
            faces.append(face)
        p=np.array([v[0] for v in records]);normal=np.array([v[1] for v in records]);uvs=np.array([v[2] for v in records]);f=np.array(faces)
        save(row['object'],p,normal,uvs,[v[3] for v in records],[v[4] for v in records],f,row['material'],'body',lod,np.array([v[5] for v in records]))
        bpy.data.objects.remove(ob,do_unlink=True)
# Submillimetre internal triangles replace generated head/hands/feet/underwear.
# Source head and hair are already part of the complete body mesh.
p=np.array([[0,0,.75],[.00001,0,.75],[0,.00001,.75]])*K
for lod in range(4):save('wdr_hidden_part',p,np.array([[0,0,1]]*3),np.array([[0,0],[1,0],[0,1]]),np.zeros((3,4)),np.array([[255,0,0,0]]*3),np.array([[0,1,2]]),'wdr_mat_body_D','hidden',lod,np.zeros(3))
(R/'build/geometry.json').write_text(json.dumps(rows,indent=2))
print('GEOMETRY_READY',len(rows),'groups; own geometry at four reduced LODs')
