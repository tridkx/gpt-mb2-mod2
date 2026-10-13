"""Add the native proxy to the editable rig without altering visible geometry."""
import bpy,sys,json
from pathlib import Path
import numpy as np
root=Path(sys.argv[sys.argv.index('--')+1]).resolve();cfg=json.loads((root/'tools/model_config.json').read_text());ident=cfg['id'];prefix=cfg.get('prefix','yqs')
bpy.ops.wm.open_mainfile(filepath=str(root/'source'/(ident+'_Rigged.blend')))
name=prefix+'_cloth_proxy'
if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
data=json.loads((root/'build/proxy_source.json').read_text());mesh=bpy.data.meshes.new(name);mesh.from_pydata(data['positions'],[],np.array(data['indices']).reshape(-1,3).tolist());mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
obj.display_type='WIRE';obj.hide_render=True;obj['role']='Native shared cloth proxy with layer links; rendered body remains unchanged'
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');modifier=obj.modifiers.new('NativeRig','ARMATURE');modifier.object=arm
for bone in arm.data.bones:obj.vertex_groups.new(name=bone.name)
bone_names=list(arm.data.bones.keys())
for i,(bones,weights) in enumerate(zip(data['bones'],data['weights'])):
    for bone,weight in zip(bones,weights):
        if weight:obj.vertex_groups[bone_names[bone]].add([i],weight/255,'REPLACE')
layer=mesh.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT');colors=np.ones((len(data['positions']),4),'f4');colors[:,3]=np.array(data['alpha'])/255;layer.data.foreach_set('color',colors.ravel())
for image in bpy.data.images:
    if image.source=='FILE':image.filepath='//../tex/'+Path(image.filepath.replace('\\','/')).name
bpy.ops.wm.save_as_mainfile(filepath=str(root/'source'/(ident+'_Rigged.blend')))
bpy.ops.export_scene.fbx(filepath=str(root/'source'/(ident+'_Rigged.fbx')),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
print('EDITABLE_PROXY_SAVED',ident,len(data['positions']))
