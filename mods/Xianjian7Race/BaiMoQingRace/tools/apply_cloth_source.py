"""Store game cloth travel paintings in editable Blend and embedded-texture FBX."""
import bpy,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'source/BaiMoQingRace_Rigged.blend'))
for image in bpy.data.images:
    if image.source=='FILE':
        texture=R/'tex'/Path(image.filepath.replace('\\','/')).name
        assert texture.is_file(),texture
        image.filepath='//../tex/'+texture.name
alphas=np.load(R/'build/cloth_alphas.npz')
for name in alphas.files:
    mesh=bpy.data.objects[name].data;a=alphas[name]
    layer=mesh.color_attributes.get('ClothDistance') or mesh.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
    colors=np.ones((len(a),4),dtype='f4');colors[:,3]=a;layer.data.foreach_set('color',colors.ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/BaiMoQingRace_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(R/'source/BaiMoQingRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
report=json.loads((R/'reports/weight_transfer.json').read_text());report['cloth']=json.loads((R/'tools/model_config.json').read_text())['cloth_enabled'];(R/'reports/weight_transfer.json').write_text(json.dumps(report,indent=2))
print('CLOTH_SOURCE_READY')
