"""Render delivered finger skinning at open/half/closed; no engine claim."""
import bpy,json,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[1];WS=R.parents[1]
sys.path[:0]=[str(R/'tools'),str(WS/'tools/asset_helpers/previewer'),str(WS/'tools/asset_helpers/tools')]
from baker.skeleton import parse_skeljson
from baker.animation import lbs
from georead import read_geo
from finger_rig import pose_world
rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
meshes=[g for path in (R/'build/final_export0/geo').glob('*.bin') for g in read_geo(path)]
hand=next(g for g in meshes if g['name']=='wdr_part_04');p=hand['pos'];faces=hand['idx'].reshape(-1,3)
for label,value in [('open',0),('half',.5),('closed',1)]:
    world=pose_world(rig,value,value);points=lbs(p,hand['bi'],hand['bw'],world@np.linalg.inv(rig['restWorld']))
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=900;s.render.resolution_y=700;s.render.resolution_percentage=100
    s.world=bpy.data.worlds.new('Finger review');s.world.color=(.3,.3,.3)
    me=bpy.data.meshes.new('Final hand');me.from_pydata(points.tolist(),[],faces.tolist());me.update();ob=bpy.data.objects.new('Final hand',me);bpy.context.collection.objects.link(ob)
    for face in me.polygons:face.use_smooth=True
    mat=bpy.data.materials.new('Hand clay');mat.use_nodes=True;mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.6,.38,.25,1);me.materials.append(mat)
    center=Vector(rig['restWorld'][26,:3,3]+rig['restWorld'][26,:3,:3]@np.array([.045,0,0]))
    offset=Vector(rig['restWorld'][26,:3,:3]@np.array([.025,-.22,.16]))
    bpy.ops.object.camera_add(location=center+offset);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.16;s.camera=cam
    for offset,power in [((.1,.2,.3),8),((-.1,-.1,.2),4)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(offset));light=bpy.context.object;light.data.energy=power;light.data.size=.2;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    s.view_settings.view_transform='AgX';s.render.filepath=str(R/'reports'/f'finger_{label}.png');bpy.ops.render.render(write_still=True)
print('FINAL_FINGER_PREVIEWS_READY')
