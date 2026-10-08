"""Source or final TPAC previews, native motion; never a game-physics test."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]/'tools/asset_helpers/tools'));sys.path.insert(0,str(ROOT.parents[1]/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
final='final' in args;quick='quick' in args
objects=[];meshes=[]
if final:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    meshes=[m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f)]
    cfg=json.loads((ROOT/'tools/model_config.json').read_text());materials={}
    for key,(file,mode) in cfg['textures'].items():
        path=next((ROOT/'build/final_export/tex').glob('rq1_'+key+'_d*.png'))
        image=bpy.data.images.load(str(path));mat=bpy.data.materials.new('rq1_'+key);mat.use_nodes=True
        bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
        mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.68
        if mode!='opaque':
            test=mat.node_tree.nodes.new('ShaderNodeMath');test.operation='GREATER_THAN';test.inputs[1].default_value=.12 if key=='lash' else .20
            mat.node_tree.links.new(tex.outputs['Alpha'],test.inputs[0]);mat.node_tree.links.new(test.outputs[0],bs.inputs['Alpha'])
        materials[mat.name]=mat
    for m in meshes:
        me=bpy.data.meshes.new(m['name']);me.from_pydata(m['pos'].tolist(),[],m['idx'].reshape(-1,3).tolist());me.update()
        uv=me.uv_layers.new(name='UVMap');coords=m['uv'].copy();coords[:,1]=1-coords[:,1]
        for loop in me.loops:uv.data[loop.index].uv=coords[loop.vertex_index]
        for f in me.polygons:f.use_smooth=True
        o=bpy.data.objects.new(m['name'],me);bpy.context.collection.objects.link(o);me.materials.append(materials[m['material']]);objects.append(o)
else:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/TianxiangRenqiu_Rigged.blend'))
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        w=np.zeros((len(o.data.vertices),28))
        for v in o.data.vertices:
            for g in v.groups:w[v.index,int(o.vertex_groups[g.group].name.rsplit('_',1)[1])]=g.weight
        bi=np.argsort(-w,axis=1)[:,:4];bw=np.take_along_axis(w,bi,axis=1)*255
        meshes.append({'pos':np.array([v.co for v in o.data.vertices]),'bi':bi,'bw':bw});objects.append(o)
        for mod in list(o.modifiers):o.modifiers.remove(mod)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12 if final else 8
s.render.resolution_x=800;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Review background');s.world.color=(.18,.18,.18);s.view_settings.view_transform='Standard'
for loc,energy,size in [((2,3,4),380,4),((-3,1,3),280,4),((0,-3,3),280,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam
prefix='final' if final else 'source'
def render(name,offset):
    points=np.concatenate([np.array([v.co for v in o.data.vertices]) for o in objects]);center=Vector((points.min(0)+points.max(0))/2)
    cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(float(np.ptp(points[:,2]))*1.14,float(np.ptp(points[:,0]))*1.35)
    s.render.filepath=str(ROOT/'reports'/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
render('rest_front',(0,4,0));render('rest_side',(4,0,0))
if not quick:
    render('rest_back',(0,-4,0));rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));previews=[]
    report=json.loads((ROOT/'reports/release_validation.json').read_text()) if final else None
    for label in ['idle','run','bow','riding']:
        anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
        frame=next(m['worst_frame'] for m in report['motions'] if m['label']==label) if report else max(1,anim['start'])+min(5,anim['frames']//3)
        skin=skin_matrices(rig,anim,frame)
        for o,m in zip(objects,meshes):
            posed=lbs(m['pos'],m['bi'],m['bw'],skin);o.data.vertices.foreach_set('co',posed.astype('f4').ravel());o.data.update()
        render(label+'_worst',(1.8,4,0));previews.append({'label':label,'frame':int(frame),'path':'reports/'+prefix+'_'+label+'_worst.png'})
        if report:
            contact_frame=next(m['skirt_leg_proxy']['worst_frame'] for m in report['motions'] if m['label']==label)
            if contact_frame!=frame:
                skin=skin_matrices(rig,anim,contact_frame)
                for o,m in zip(objects,meshes):
                    posed=lbs(m['pos'],m['bi'],m['bw'],skin);o.data.vertices.foreach_set('co',posed.astype('f4').ravel());o.data.update()
                render(label+'_contact',(2.8,4,0));previews.append({'label':label,'frame':int(contact_frame),'path':'reports/'+prefix+'_'+label+'_contact.png','reason':'worst skirt proxy contact'})
    if final:(ROOT/'reports/final_preview_manifest.json').write_text(json.dumps({'package_sha256':report['final_package_sha256'],'source':'Final TPAC re-export with decoded textures and quantized weights','game_cloth_solver_used':False,'previews':previews},indent=2))
print('PREVIEWS_READY',prefix)
