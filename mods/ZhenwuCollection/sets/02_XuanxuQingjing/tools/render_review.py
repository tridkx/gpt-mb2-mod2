"""Source or final TPAC previews, native motion; never a game-physics test."""
import bpy,sys,json,struct
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/tools'));sys.path.insert(0,str(next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
final='final' in args;quick='quick' in args
objects=[];meshes=[]
def normals_from_export(file,rows):
    data=file.read_bytes();off=12;result={}
    for m in rows:
        for field in range(3):
            length=struct.unpack_from('<I',data,off)[0];off+=4+length
            if field==0:off+=4
        n=m['nverts'];flags=m['flags'];off+=8+24+4+n*12
        if flags&1:result[m['name']]=np.frombuffer(data,'<f4',n*3,off).reshape(n,3).copy();off+=n*12
        off+=n*8
        if flags&2:off+=n*8
        if flags&4:off+=n*4
        if flags&8:off+=n*4
        if flags&16:off+=n*16
        if flags&32:off+=n*4
        off+=n*4+m['nidx']*4
    assert off==len(data)
    return result
if final:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    exported_normals={}
    for file in (ROOT/'build/final_export/geo').glob('*.bin'):
        rows=read_geo(file);meshes.extend(rows);exported_normals.update(normals_from_export(file,rows))
    cfg=json.loads((ROOT/'tools/model_config.json').read_text());materials={}
    for key,(file,mode) in cfg['textures'].items():
        path=next((ROOT/'build/final_export/tex').glob('zw_xuanxu_'+key+'_d*.png'))
        image=bpy.data.images.load(str(path));mat=bpy.data.materials.new('zw_xuanxu_'+key);mat.use_nodes=True
        bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
        mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.68
        if mode!='opaque':
            test=mat.node_tree.nodes.new('ShaderNodeMath');test.operation='GREATER_THAN';test.inputs[1].default_value=cfg.get('material_overrides',{}).get(key,{}).get('alphaTest',.12 if key=='lash' else .20)
            mat.node_tree.links.new(tex.outputs['Alpha'],test.inputs[0])
            if mode!='opaque':
                blend=mat.node_tree.nodes.new('ShaderNodeMath');blend.operation='MULTIPLY'
                mat.node_tree.links.new(test.outputs[0],blend.inputs[0]);mat.node_tree.links.new(tex.outputs['Alpha'],blend.inputs[1])
                mat.node_tree.links.new(blend.outputs[0],bs.inputs['Alpha'])
            else:mat.node_tree.links.new(test.outputs[0],bs.inputs['Alpha'])
        materials[mat.name]=mat
    for m in meshes:
        me=bpy.data.meshes.new(m['name']);me.from_pydata(m['pos'].tolist(),[],m['idx'].reshape(-1,3).tolist());me.update()
        uv=me.uv_layers.new(name='UVMap');coords=m['uv'].copy();coords[:,1]=1-coords[:,1]
        for loop in me.loops:
            u=coords[loop.vertex_index].copy()
            if m['name']=='zw_xuanxu_head_04':
                if 'flip_lash_v' in args:u[1]=1-u[1]
                if 'flip_lash_u' in args:u[0]=1-u[0]
            uv.data[loop.index].uv=u
        for f in me.polygons:f.use_smooth=True
        me.normals_split_custom_set_from_vertices(exported_normals[m['name']])
        o=bpy.data.objects.new(m['name'],me);bpy.context.collection.objects.link(o);me.materials.append(materials[m['material']]);objects.append(o)
else:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/ZhenwuXuanxu_Rigged.blend'))
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
if 'flip_lash_v' in args:prefix+='_lash_vflip'
if 'flip_lash_u' in args:prefix+='_lash_uflip'
def render(name,offset):
    points=np.concatenate([np.array([v.co for v in o.data.vertices]) for o in objects]);center=Vector((points.min(0)+points.max(0))/2)
    cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(float(np.ptp(points[:,2]))*1.14,float(np.ptp(points[:,0]))*1.35)
    s.render.filepath=str(ROOT/'reports'/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
if 'face_only' not in args:render('rest_front',(0,4,0));render('rest_side',(4,0,0))
if 'face' in args:
    s.render.resolution_x=1000;s.render.resolution_y=1000;s.cycles.samples=32
    eye=next(o for o in objects if o.name=='zw_xuanxu_head_00');center=Vector(np.array([v.co for v in eye.data.vertices]).mean(0));center.z+=.012
    cam.location=center+Vector((0,3,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.26
    face_views=[('all',[])] if 'eye_variant' in args else [('all',[]),('no_lash',['zw_xuanxu_head_04']),('eye_only',[o.name for o in objects if o.name!='zw_xuanxu_head_00'])]
    for label,hidden in face_views:
        for o in objects:o.hide_render=o.name in hidden
        s.render.filepath=str(ROOT/'reports'/(prefix+'_face_'+label+'.png'));bpy.ops.render.render(write_still=True)
    for o in objects:o.hide_render=False
if not quick:
    render('rest_back',(0,-4,0));rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));previews=[{'label':'rest_'+view,'path':'reports/'+prefix+'_rest_'+view+'.png'} for view in ['front','side','back']]
    if 'face' in args:previews.extend([{'label':'face_'+label,'path':'reports/'+prefix+'_face_'+label+'.png'} for label in ['all','no_lash','eye_only']])
    report=json.loads((ROOT/'reports/release_validation.json').read_text()) if final else None
    for label in ['idle','run','bow','riding']:
        anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
        frame=next(m['worst_frame'] for m in report['motions'] if m['label']==label) if report else max(1,anim['start'])+min(5,anim['frames']//3)
        skin=skin_matrices(rig,anim,frame)
        for o,m in zip(objects,meshes):
            posed=lbs(m['pos'],m['bi'],m['bw'],skin);o.data.vertices.foreach_set('co',posed.astype('f4').ravel());o.data.update()
            if final:
                normal=np.einsum('nv,nvij,nj->ni',m['bw']/255.,skin[m['bi'],:3,:3],exported_normals[m['name']]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8);o.data.normals_split_custom_set_from_vertices(normal)
        render(label+'_worst',(1.8,4,0));previews.append({'label':label,'frame':int(frame),'path':'reports/'+prefix+'_'+label+'_worst.png'})
        if report:
            contact_frame=next(m['skirt_leg_proxy']['worst_frame'] for m in report['motions'] if m['label']==label)
            if contact_frame!=frame:
                skin=skin_matrices(rig,anim,contact_frame)
                for o,m in zip(objects,meshes):
                    posed=lbs(m['pos'],m['bi'],m['bw'],skin);o.data.vertices.foreach_set('co',posed.astype('f4').ravel());o.data.update()
                    normal=np.einsum('nv,nvij,nj->ni',m['bw']/255.,skin[m['bi'],:3,:3],exported_normals[m['name']]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-8);o.data.normals_split_custom_set_from_vertices(normal)
                render(label+'_contact',(2.8,4,0));previews.append({'label':label,'frame':int(contact_frame),'path':'reports/'+prefix+'_'+label+'_contact.png','reason':'worst skirt proxy contact'})
    if final and (ROOT/'reports/veil_travel_validation.json').exists():
        travel=json.loads((ROOT/'reports/veil_travel_validation.json').read_text())
        frame=next(m['largest_travel_frame'] for m in travel['motions'] if m['label']=='weapon_slash')
        anim=parse_animjson(json.loads((ROOT/'reports/weapon_slash.json').read_text()));skin=skin_matrices(rig,anim,frame)
        for o,m in zip(objects,meshes):
            posed=lbs(m['pos'],m['bi'],m['bw'],skin);o.data.vertices.foreach_set('co',posed.astype('f4').ravel());o.data.update()
        render('weapon_slash',(1.8,4,0));previews.append({'label':'weapon_slash','frame':frame,'path':'reports/final_weapon_slash.png','scope':'native skeletal pose only; no weapon mesh, IK or cloth solver'})
        arrays=np.load(ROOT/'build/rig_arrays.npz');plan=json.loads((ROOT/'reports/veil_distance_plan.json').read_text())
        for bone,side in [(17,'left'),(24,'right')]:
            panel=next(p for p in plan['panels'] if p['bone']==bone)
            roots=arrays[panel['mesh']+'_P'][panel['fixed_vertices']]
            center=Vector((roots@skin[bone,:3,:3].T+skin[bone,:3,3]).mean(0));center.z-=.24
            cam.location=center+Vector((1.8,4,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.05
            label='weapon_cuff_'+side;s.render.filepath=str(ROOT/'reports'/('final_'+label+'.png'));bpy.ops.render.render(write_still=True)
            previews.append({'label':label,'frame':frame,'path':'reports/final_'+label+'.png','scope':'cuff attachment close-up, skeletal pose only'})
    if final:(ROOT/'reports/final_preview_manifest.json').write_text(json.dumps({'package_sha256':report['final_package_sha256'],'source':'Final TPAC re-export with decoded textures and quantized weights','game_cloth_solver_used':False,'previews':previews},indent=2))
print('PREVIEWS_READY',prefix)
