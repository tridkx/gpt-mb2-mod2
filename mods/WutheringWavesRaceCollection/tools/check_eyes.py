import bpy,sys,json
from pathlib import Path
from mathutils import Vector
S=Path(__file__).resolve().parents[1];W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir());sys.path.insert(0,str(W/'tools/pmx_race_pipeline'))
from source_preview import preview
r=S/'JinhsiRace';preview(r);s=bpy.context.scene;s.render.resolution_x=600;s.render.resolution_y=600
s.camera.location=Vector((0,4,1.49));s.camera.rotation_euler=(Vector((0,0,1.49))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.32
for label,hide in [('with_hi',False),('without_hi',True)]:
 bpy.data.objects['ww_jinhsi_part_10'].hide_render=hide;s.render.filepath=str(S/'reports'/('eyes_'+label+'.png'));bpy.ops.render.render(write_still=True)
