"""Consistent close rear/side views from final TPAC, native inventory idle."""
import bpy,sys,json
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
# Reuse the established material/geometry importer, stopping before its renders.
code=(ROOT/'tools/render_review.py').read_text().split('s=bpy.context.scene;')[0]
code=code.replace("ROOT/'build/final_export/geo'", "ROOT/'build/hair_shape_final_export/geo'")
sys.argv+=['--','final'] if '--' not in sys.argv else ['final']
exec(compile(code,str(ROOT/'tools/render_review.py'),'exec'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=750;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Hair review');s.world.color=(.2,.2,.2);s.view_settings.view_transform='Standard'
for loc,energy in [((2,-3,3),380),((-3,-2,3),330),((0,2,4),250)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=energy;light.data.size=3
 light.rotation_euler=(Vector((0,0,1.3))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=.93;s.camera=cam
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));anim=parse_animjson(json.loads((ROOT/'reports/idle.json').read_text()))
diagnosis=json.loads((ROOT/'reports/hair_shape_diagnosis.json').read_text());frame=min((r for r in diagnosis['before'] if r['animation']=='idle'),key=lambda r:r['minimum_gap_m'])['frame']
skin=skin_matrices(rig,anim,frame)
for state,folder in [('before','final_export'),('after','hair_shape_final_export')]:
 data={m['name']:m for f in (ROOT/'build'/folder/'geo').glob('*.bin') for m in read_geo(f)}
 for o in objects:
  m=data[o.name];p=lbs(m['pos'],m['bi'],m['bw'],skin)
  me=o.data;me.clear_geometry();me.from_pydata(p.tolist(),[],m['idx'].reshape(-1,3).tolist());me.update()
  uv=me.uv_layers.new(name='UVMap');coords=m['uv'].copy();coords[:,1]=1-coords[:,1]
  for loop in me.loops:uv.data[loop.index].uv=coords[loop.vertex_index]
  for poly in me.polygons:poly.use_smooth=True
 center=Vector((0,0,1.32))+Vector(skin[11,:3,3])
 for view,offset in [('side',(3,-.7,0)),('back',(.4,-3,0))]:
  cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=str(ROOT/f'reports/hair_{state}_idle_{view}.png');bpy.ops.render.render(write_still=True)
(ROOT/'reports/hair_shape_preview.json').write_text(json.dumps({'animation':'anim_inventory_idle','frame':frame,'source':'final TPAC exports','scope':'native skeletal pose without cloth physics','paths':[f'reports/hair_{state}_idle_{view}.png' for state in ['before','after'] for view in ['side','back']]},indent=2))
