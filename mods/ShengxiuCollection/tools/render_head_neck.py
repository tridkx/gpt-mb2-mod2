"""Compare actual v1.1.5/candidate head and hair in the strongest idle pitch."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'tools/render_hair_fit.py').read_text()
code=code.replace('build/hair_shape_final_export/geo','build/head_neck_final_export/geo')
code=code.replace("('before','final_export'),('after','hair_shape_final_export')","('before','hair_shape_final_export'),('after','head_neck_final_export')")
start=code.index('diagnosis=json.loads');end=code.index('skin=skin_matrices',start)
code=code[:start]+"frame=max(range(1,anim['frames']),key=lambda f:abs(skin_matrices(rig,anim,f)[13,2,1]))\n"+code[end:]
code=code.replace("[('side',(3,-.7,0)),('back',(.4,-3,0))]","[('side',(3,-.7,0)),('back',(.4,-3,0)),('neck',(3,0,0))]")
code=code.replace('  cam.location=center+',"  cam.data.ortho_scale=.45 if view=='neck' else .93\n  target=Vector(np.array([v.co for v in next(o for o in objects if o.name=='sx_mingyu_head_07').data.vertices]).mean(0))+Vector((0,0,-.065)) if view=='neck' else center\n  cam.location=target+")
code=code.replace('(center-cam.location)','(target-cam.location)').replace('reports/hair_shape_preview.json','reports/head_neck_preview.json').replace('reports/hair_','reports/head_neck_')
code=code.replace("for view in ['side','back']","for view in ['side','back','neck']")
exec(compile(code,__file__,'exec'))
