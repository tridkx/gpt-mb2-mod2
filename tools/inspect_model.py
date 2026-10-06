import bpy, json, os
from mathutils import Vector
ROOT = r'D:\gpt-mb2-mod2'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT, 'model.fbx'))
def describe(obj):
    result = {'name':obj.name,'type':obj.type,'location':list(obj.location),'scale':list(obj.scale),'rotation':list(obj.rotation_euler)}
    if obj.type == 'MESH':
        pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        result.update(vertices=len(pts), faces=len(obj.data.polygons), bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)], materials=[m.name if m else None for m in obj.data.materials], groups=[g.name for g in obj.vertex_groups], uvs=[a.name for a in obj.data.uv_layers])
    if obj.type == 'ARMATURE':
        result['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(obj.matrix_world @ b.head_local),'tail':list(obj.matrix_world @ b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in obj.data.bones]
    return result
report = {'model':[describe(o) for o in bpy.context.scene.objects], 'materials':[]}
for m in bpy.data.materials:
    report['materials'].append({'name':m.name,'images':[{'name':n.image.name,'path':n.image.filepath} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m.use_nodes else []})
for img in bpy.data.images:
    guess=os.path.join(ROOT,'tex',os.path.basename(img.filepath.replace('\\','/')))
    if os.path.isfile(guess): img.filepath=guess; img.reload()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'inspection.blend'))
bpy.ops.import_scene.fbx(filepath=r'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord\modding_resources\skeletons\human_skeleton.fbx',use_anim=False)
report['all_objects']=[describe(o) for o in bpy.context.scene.objects]
os.makedirs(os.path.join(ROOT,'reports'),exist_ok=True)
with open(os.path.join(ROOT,'reports','inspection.json'),'w',encoding='utf-8') as f: json.dump(report,f,indent=2,ensure_ascii=False)
print('INSPECTION_READY')
