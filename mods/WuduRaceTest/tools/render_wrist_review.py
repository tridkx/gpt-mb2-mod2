"""Close-up wrist comparison in sampled native actions; cloth solver is excluded."""
import bpy,json,sys,subprocess
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build'
sys.path[:0]=[str(WS/'tools/asset_helpers/tools'),str(WS/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
baseline=B/'hand_baseline_v0.2.0';old_export=baseline/'export0'
if (baseline/'wdr.tpac').exists() and not old_export.exists():
    subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(baseline/'wdr.tpac'),str(old_export),'0'],check=True,stdout=subprocess.DEVNULL)
report=json.loads((R/'reports/hand_validation.json').read_text());plan={x['material']:x for x in json.loads((B/'rig_manifest.json').read_text())}
for label in ['sword','bow']:
    frame=next(x['preview_frame'] for x in report['native_animation_samples'] if x['animation']==label)
    animation=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()))
    targets=[('after',B/'final_export0',R/'reports/final_skeleton.json')]
    if old_export.exists():targets.append(('before',old_export,baseline/'final_skeleton.json'))
    for version,folder,skeleton in targets:
        rig=parse_skeljson(json.loads(skeleton.read_text()));world=rig['restWorld'].copy()
        for i in range(rig['boneCount']):
            local=rig['restLocal'][i].copy();local[:3,:3]=q2R(animation['quat'][i,frame]) if i<28 else local[:3,:3];parent=rig['parent'][i]
            if parent<0:local[:3,3]+=animation['rootPos'][frame]
            world[i]=local if parent<0 else world[parent]@local
        skin=world@np.linalg.inv(rig['restWorld'])
        if version=='after':
            camera_center=world[26,:3,3]+world[26,:3,0]*.025
            camera_offset=world[26,:3,:3]@np.array([.04,-.20,.12])
        bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
        s.world=bpy.data.worlds.new('Wrist review');s.world.color=(.3,.3,.3)
        for path in (folder/'geo').glob('*.bin'):
            for g in read_geo(path):
                if g['name'] not in ['wdr_part_02','wdr_part_04','wdr_part_07','wdr_part_09']:continue
                p=lbs(g['pos'],g['bi'],g['bw'],skin);me=bpy.data.meshes.new(g['name']);me.from_pydata(p.tolist(),[],g['idx'].reshape(-1,3).tolist());me.update();ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob)
                uv=me.uv_layers.new(name='UVMap')
                for loop in me.loops:u=g['uv'][loop.vertex_index];uv.data[loop.index].uv=(u[0],1-u[1])
                for face in me.polygons:face.use_smooth=True
                info=plan[g['material']];mat=bpy.data.materials.new(g['material']);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(R/'tex'/info['texture']));mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
                if info['cutout']:
                    threshold=mat.node_tree.nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.25;mat.node_tree.links.new(node.outputs['Alpha'],threshold.inputs[0]);mat.node_tree.links.new(threshold.outputs[0],bs.inputs['Alpha'])
                me.materials.append(mat)
        center=Vector(camera_center);bpy.ops.object.camera_add(location=center+Vector(camera_offset));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.23;s.camera=cam
        for offset,power in [((.1,.2,.3),8),((-.1,-.1,.2),4)]:
            bpy.ops.object.light_add(type='AREA',location=center+Vector(offset));light=bpy.context.object;light.data.energy=power;light.data.size=.25;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
        s.view_settings.view_transform='AgX';s.render.filepath=str(R/'reports'/f'wrist_{label}_{version}.png');bpy.ops.render.render(write_still=True)
print('WRIST_NATIVE_ACTION_PREVIEWS_READY')
