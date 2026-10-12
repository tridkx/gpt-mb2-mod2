"""Paint only the separate skirt panel; preserve waist roots and all geometry."""
import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'source/TianxiangGirlT2Race_Rigged.blend'))
cfg=json.loads((R/'tools/model_config.json').read_text())
o=bpy.data.objects[cfg['skirt_object']];p=np.array([v.co for v in o.data.vertices])
# The source has a waist overlay and two separate long panels attaching at
# about .768 m. Determine each component's upper attachment independently.
parent=list(range(len(p)))
def root(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for e in o.data.edges:i,j=e.vertices;parent[root(i)]=root(j)
groups={}
for i in range(len(p)):groups.setdefault(root(i),[]).append(i)
a=np.zeros(len(p));components=[]
for ids in groups.values():
    q=p[ids];top=float(q[:,2].max());height=float(np.ptp(q[:,2]))
    # Tiny metallic/flower ornaments remain skeletal; cloth panels and long
    # ribbons have explicit fixed upper attachments.
    if height>.4:
        distance=np.maximum(top-cfg['cloth_root_band_m']-q[:,2],0)
        travel=np.minimum(.10+distance*cfg['cloth_travel_slope'],cfg['cloth_max_travel_m'])
        travel[distance<.005]=0;a[ids]=travel
    components.append(dict(vertices=len(ids),top_m=top,height_m=height,fixed_vertices=int((a[ids]==0).sum()),active_vertices=int((a[ids]>0).sum())))
layer=o.data.color_attributes.get('ClothDistance') or o.data.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
colors=np.ones((len(a),4),dtype='f4');colors[:,3]=a;layer.data.foreach_set('color',colors.ravel())
assert (a==0).sum()>10 and (a>0).sum()>100
for im in bpy.data.images:
    if im.source=='FILE':
        im.filepath='//../tex/'+Path(im.filepath.replace('\\','/')).name
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/TianxiangGirlT2Race_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/TianxiangGirlT2Race_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
(R/'reports/cloth_paint.json').write_text(json.dumps(dict(mesh=o.name,fixed_vertices=int((a==0).sum()),active_vertices=int((a>0).sum()),component_root_band_m=cfg['cloth_root_band_m'],max_travel_m=float(a.max()),lods=cfg['cloth_lods'],components=components),indent=2))
