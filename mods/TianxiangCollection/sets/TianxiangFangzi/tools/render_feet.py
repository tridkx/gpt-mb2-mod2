import sys
from pathlib import Path
script=Path(__file__).with_name('render_review.py');sys.argv=['blender','--','final','quick']
code=script.read_text().split("if 'face_only' not in args:")[0];env={'__file__':str(script)};exec(compile(code,str(script),'exec'),env)
bpy=env['bpy'];s=env['s'];cam=env['cam'];Vector=env['Vector'];ROOT=env['ROOT'];center=Vector((0,0,.10));cam.location=center+Vector((.5,1,.2));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.60;s.render.resolution_x=1000;s.render.resolution_y=500
for label,hide_skin in [('all',False),('no_skin',True)]:
    bpy.data.objects['fz5_legs_06'].hide_render=hide_skin;s.render.filepath=str(ROOT/'build'/('feet_'+label+'.png'));bpy.ops.render.render(write_still=True)
