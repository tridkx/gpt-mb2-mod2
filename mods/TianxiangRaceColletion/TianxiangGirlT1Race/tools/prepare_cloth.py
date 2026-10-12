"""Paint only the separate skirt panel; preserve waist roots and all geometry."""
import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'source/TianxiangGirlT1Race_Rigged.blend'))
o=bpy.data.objects['txgirl1_part_12'];p=np.array([v.co for v in o.data.vertices])
# Source skirt attaches around z=.86-.878 m. The top 30 mm remains fixed.
distance=np.maximum(.845-p[:,2],0)
a=np.minimum(distance*.75,.32);a[a<.006]=0
layer=o.data.color_attributes.get('ClothDistance') or o.data.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
colors=np.ones((len(a),4),dtype='f4');colors[:,3]=a;layer.data.foreach_set('color',colors.ravel())
assert (a==0).sum()>10 and (a>0).sum()>100
for im in bpy.data.images:
    if im.source=='FILE':
        im.filepath='//../tex/'+Path(im.filepath.replace('\\','/')).name
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/TianxiangGirlT1Race_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/TianxiangGirlT1Race_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
(R/'reports/cloth_paint.json').write_text(json.dumps(dict(mesh=o.name,fixed_vertices=int((a==0).sum()),active_vertices=int((a>0).sum()),root_band_m=[.845,.878],max_travel_m=float(a.max()),lods=[0,1]),indent=2))
