"""Render shoulder side views and actual native running poses without launching the game."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices
rig=parse_skeljson(json.load(open(ROOT/'reports/human_skeleton.json')))
idle=parse_animjson(json.load(open(ROOT/'reports/idle.json')))
run=parse_animjson(json.load(open(ROOT/'reports/run.json')))

versions=[('before',ROOT/'build/movement_baseline/rigged.blend'),('after',ROOT/'source/TianxiangT5_Rigged.blend')]
prefix='motion'
views=[
    ('shoulder_side',idle,1,'side',(0,0,1.28),.83),
    ('run_side',run,6,'side',(0,0,.86),1.90),
    ('run_back',run,18,'back',(0,0,.84),1.90),
]
if '--posture' in sys.argv:
    prefix='posture'
    versions[0]=('before',ROOT/'build/posture_baseline/rigged.blend')
    views=[
        ('front',idle,1,'front',(0,0,1.24),1.24),
        ('side',idle,1,'side',(0,0,1.22),1.14),
        ('run_side',run,6,'side',(0,0,.86),1.90),
    ]
if '--after-only' in sys.argv:versions=versions[1:]
if '--grip' in sys.argv:
    prefix='grip'
    versions=[('before',ROOT/'build/grip_baseline/rigged.blend'),('after',ROOT/'source/TianxiangT5_Rigged.blend')]
    block=parse_animjson(json.load(open(ROOT/'reports/grip_twohanded_block.json')))
    thrust=parse_animjson(json.load(open(ROOT/'reports/grip_twohanded_thrust.json')))
    views=[('block',block,34,'grip',None,.80),('thrust',thrust,102,'grip',None,.80),
           ('shoulder_side',idle,1,'side',(0,0,1.25),1.12)]
for version,file in versions:
    bpy.ops.wm.open_mainfile(filepath=str(file))
    # Baseline .blend is extracted into build/, so resolve its relative textures.
    for image in bpy.data.images:
        guess=ROOT/'tex'/image.filepath.replace('\\','/').split('/')[-1]
        if guess.is_file():image.filepath=str(guess);image.reload()
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith('_cloth_preview')]
    base={};weights={};normals={}
    for o in objects:
        base[o.name]=np.array([v.co for v in o.data.vertices])
        w=np.zeros((len(o.data.vertices),28))
        for v in o.data.vertices:
            for g in v.groups:w[v.index,int(o.vertex_groups[g.group].name.rsplit('_',1)[1])]=g.weight
        weights[o.name]=w
        n=np.zeros_like(base[o.name]);counts=np.zeros((len(n),1))
        for loop,normal in zip(o.data.loops,o.data.corner_normals):
            n[loop.vertex_index]+=normal.vector;counts[loop.vertex_index]+=1
        n/=np.maximum(counts,1);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-9);normals[o.name]=n
        for modifier in list(o.modifiers):o.modifiers.remove(modifier)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.world.color=(.20,.20,.20)
    scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='Standard'
    for loc,energy,size in [((2,3,4),450,4),((-3,1,3),350,4),((0,-3,3),350,3)]:
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object
        light.data.energy=energy;light.data.shape='DISK';light.data.size=size
        light.rotation_euler=(Vector((0,0,1.0))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
    for label,anim,frame,view,center,scale in views:
        skin=skin_matrices(rig,anim,frame)
        for o in objects:
            p=base[o.name];w=weights[o.name];h=np.c_[p,np.ones(len(p))]
            posed=sum(w[:,i,None]*(h@skin[i].T)[:,:3] for i in range(28))
            normal=sum(w[:,i,None]*(normals[o.name]@skin[i,:3,:3].T) for i in range(28))
            normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
            for vertex,co in zip(o.data.vertices,posed):vertex.co=co
            o.data.normals_split_custom_set_from_vertices(normal.tolist())
        if view=='grip':
            # Same native hand-bone camera target in both versions, independent
            # of the displaced baseline hands. No synthetic weapon is rendered.
            centers=[(skin[i] @ np.r_[rig['restWorld'][i][:3,3],1])[:3] for i in [19,26]]
            center=np.mean(centers,axis=0)+[0,0,-.04]
        offset={'side':(4,0,0),'front':(0,4,0),'back':(0,-4,0),'grip':(2,4,1)}[view]
        center=Vector(center);cam.location=center+Vector(offset)
        cam.data.ortho_scale=scale;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(ROOT/f'reports/{prefix}_{version}_{label}.png')
        bpy.ops.render.render(write_still=True)
