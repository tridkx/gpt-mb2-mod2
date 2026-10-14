"""Reuse the project's studio renderer for isolated CPU mapping comparisons."""
from pathlib import Path
import json

R = Path(__file__).resolve().parents[1]
code = (R/'tools/render_final.py').read_text().split("render('rest_front'")[0]
code = code.replace("folder=ROOT/('build/final_export_lod'+str(lod))", "folder=ROOT/'build/mapping_candidate_lod0'")
code = code.replace("if not m['name'].startswith('yqs_hidden')", "if not m['name'].startswith(('yqs_hidden','yqs_cloth_proxy'))")
code = code.replace("ROOT/'reports'/", "ROOT/'reports/experiments/simplified_skirt_2026-10-14'/")
exec(compile(code, str(R/'tools/render_final.py'), 'exec'))
out = ROOT/'reports/experiments/simplified_skirt_2026-10-14'
out.mkdir(parents=True, exist_ok=True)
rig = parse_skeljson(json.loads((ROOT/'reports/final_skeleton.json').read_text()))
anim = parse_animjson(json.loads((ROOT/'reports/ui_neutral_female.json').read_text()))
skin = skin_matrices(rig, anim, max(1, anim['start']))
for o, m in zip(objects, meshes):
    points = lbs(m['pos'], m['bi'], m['bw'], skin)
    o.data.vertices.foreach_set('co', points.astype('f4').ravel())
    o.data.update()
for label, direction in [('front',(0,4,0)), ('side',(4,0,0)), ('back',(0,-4,0))]:
    render('reference_'+label, direction)
for o, m in zip(objects, meshes):
    path = ROOT/'build'/(m['name']+'_mapped_settled.npz')
    if path.exists():
        points = np.load(path)['after']
        assert len(points) == len(o.data.vertices)
        o.data.vertices.foreach_set('co', points.astype('f4').ravel())
        o.data.update()
for label, direction in [('front',(0,4,0)), ('side',(4,0,0)), ('back',(0,-4,0))]:
    render('settled_'+label, direction)
motion_report=ROOT/'reports/simplified_skirt_motion.json'
if motion_report.exists():
    for entry in json.loads(motion_report.read_text())['motions']:
        name=entry['motion']
        anim=parse_animjson(json.loads((ROOT/'reports'/(name+'.json')).read_text()))
        skin=skin_matrices(rig,anim,entry['worst_source_frame'])
        for o,m in zip(objects,meshes):
            path=ROOT/'build/simplified_skirt_motion'/name/(m['name']+'_mapped.npz')
            points=np.load(path)['after'] if path.exists() else lbs(m['pos'],m['bi'],m['bw'],skin)
            o.data.vertices.foreach_set('co',points.astype('f4').ravel());o.data.update()
        render('motion_'+name+'_front',(0,4,0))
        render('motion_'+name+'_side',(4,0,0))
