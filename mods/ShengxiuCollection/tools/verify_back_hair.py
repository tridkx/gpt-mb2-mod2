"""Final hair-only geometry/cloth and complete native posture cycles."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'tools/verify_hair_shape.py').read_text()
code=code.replace('hair_shape','back_hair').replace('v1.1.5','v1.1.7')
code=code.replace('back_hair_baseline_v1.1.4','hair_shape_baseline_v1.1.4').replace('from back_hair_analysis','from hair_shape_analysis')
code=code.replace('reports/hair_clearance_validation.json','reports/head_neck_validation.json').replace('>.012','>.008').replace('Rear travel is 12mm','Rear travel is 8mm')
code=code.replace("assert sha(xml)==previous['collision_xml_sha256']", "assert sha(xml)==json.loads((ROOT/'reports/free_hair_collision_fit.json').read_text())['xml_sha256']")
code=code.replace('Rear travel is 8mm before quantization; front locks keep original distance.', 'Rear travel increases from scalp roots to 200mm at tips; front locks keep original distance. Clearance metrics describe the skinned reference; dynamic clearance is collision-dependent and examined separately in free_hair_diagnostic.json.')
# User accepts visually minor clipping. Bound isolated reference intersections
# instead of moving the whole hair sheet outward to make every sample positive.
code=code.replace("assert all(r['inside_vertices']==0 for r in metrics)","assert all(r['inside_vertices']/max(r['covered_vertices'],1)<.001 and r['minimum_gap_m']>-.005 for r in metrics)")
if '--reuse-poses' in sys.argv:
 import json,hashlib
 from cloth_payload import read
 candidate=ROOT/'build/back_hair_candidate_v1.1.7.tpac'
 report=json.loads((ROOT/'reports/back_hair_validation.json').read_text())
 assert report['status']=='pass' and report['final_package_sha256']==hashlib.sha256(candidate.read_bytes()).hexdigest()
 assert report['collision_xml_sha256']==hashlib.sha256((ROOT/'module/ShengxiuCollection/ModuleData/cloth_bodies.xml').read_bytes()).hexdigest()
 mesh=next(json.loads(p.read_text()) for p in (ROOT/'build/back_hair_final_dump').glob('*.mesh.json') if json.loads(p.read_text())['name']=='sx_mingyu_head_00')
 data=read(ROOT/'build/back_hair_final_dump'/f"sx_mingyu_head_{mesh['guid']}.bin")
else:
 exec(compile(code,__file__,'exec'))

# Source preservation and the new distance gradient must match the final blob.
import numpy as np,json,xml.etree.ElementTree as ET
import subprocess
baseline=np.load(ROOT/'build/back_hair_baseline_v1.1.6/rig_arrays.npz')
current=np.load(ROOT/'build/rig_arrays.npz')
for key in baseline.files:
 if key.startswith('sx_mingyu_head_00_'):continue
 assert np.array_equal(baseline[key],current[key]),key
assert np.array_equal(baseline['sx_mingyu_head_00_A']==0,current['sx_mingyu_head_00_A']==0)
rows=json.loads((ROOT/'reports/back_hair_build.json').read_text())
assert np.isclose(data['max_distances'].max(),.2)
fixed=data['max_distances']==0
assert np.all(fixed[:data['normal_start']]) and not np.any(fixed[data['normal_start']:])
oldbody=ET.parse(ROOT/'build/back_hair_baseline_v1.1.6/cloth_bodies.xml').getroot()
newbody=ET.parse(ROOT/'module/ShengxiuCollection/ModuleData/cloth_bodies.xml').getroot()
assert ET.tostring(next(b for b in oldbody if b.get('name')=='sx_mingyu_leg_collision'))==ET.tostring(next(b for b in newbody if b.get('name')=='sx_mingyu_leg_collision'))
report['source_non_hair_arrays_identical_to_v1_1_6']=True
report['scalp_fixed_roots_unchanged']=True
report['maximum_solver_travel_m']=float(data['max_distances'].max())
report['accepted_leg_collision_body_unchanged']=True
metadata=json.loads(subprocess.check_output(['dotnet',str(ROOT/'build/cloth_probe/NativeClothProbe.dll'),str(candidate),'sx_mingyu_head']))
hairmeta=next(m for m in metadata[0]['meshes'] if m['Name']=='sx_mingyu_head_00')
assert np.isclose(hairmeta['ClothingMaterial']['BendingStiffness'],.18)
assert hairmeta['ClothingMaterial']['Gravity']==7 and hairmeta['UnknownFloat1']==1
assert hairmeta['alpha_max']==51 and hairmeta['UnknownInt3']==120
report['final_hair_cloth_material']=hairmeta['ClothingMaterial']
report['final_hair_iteration_frequency']=hairmeta['UnknownInt3']
report['minor_reference_clipping_acceptance']='Per native pose: less than 0.1% rear-ray samples inside and penetration below 5mm. User prioritizes silhouette and permits visually minor clipping; a ray diagnostic cannot itself judge game appearance.'
(ROOT/'reports/back_hair_validation.json').write_text(json.dumps(report,indent=2))
