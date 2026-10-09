"""Reread final candidate, verify geometry/cloth and actual posterior triangle gaps."""
import json,sys,hashlib,subprocess
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from hair_shape_analysis import ROOT,WS,read_geo,evaluate
sys.path.insert(0,str(WS/'tools'))
from cloth_compiler.cloth_payload import read,decode_positions
from cloth_compiler.validation import check_structure
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=ROOT/'build';arrays=np.load(build/'rig_arrays.npz');old=np.load(build/'hair_shape_baseline_v1.1.4/rig_arrays.npz')
tree=cKDTree(arrays['sx_mingyu_head_00_P']);rows=[];allmeshes=[]
for lod in range(4):
 folder=build/('hair_shape_final_export'+('' if lod==0 else '_lod'+str(lod)))
 meshes=[m for p in (folder/'geo').glob('*.bin') for m in read_geo(p)]
 allmeshes+=meshes
 for m in meshes:
  assert np.isfinite(m['pos']).all() and np.isfinite(m['uv']).all()
  assert np.all(m['bw'].sum(1)==255) and m['bi'].max()<28
  assert m['idx'].min()>=0 and m['idx'].max()<len(m['pos'])
  m['name']=m['name'].split('.lod')[0]
 hair=next(m for m in meshes if m['name']=='sx_mingyu_head_00')
 distance,index=tree.query(hair['pos']);original=old['sx_mingyu_head_00_P'][index]
 mask=(original[:,1]<-.025)&(original[:,2]<1.50)
 # Lower LOD decimation may move vertices; nearest source records classify strands.
 metrics=evaluate(meshes,posterior_mask=mask,sample_faces=True,full_cycles=True)
 for metric in metrics:metric['lod']=lod
 rows+=metrics
 print('LOD',lod,[(label,round(min(r['minimum_gap_m'] for r in metrics if r['animation']==label),5),max(r['inside_vertices'] for r in metrics if r['animation']==label)) for label in ['rest','idle','run','bow','riding']],flush=True)
 # The primary repair must have a full rear cloth travel budget outside the coat.
 assert min(r['minimum_gap_m'] for r in metrics if r['animation'] in ['rest','idle','run'])>.012
 assert all(r['inside_vertices']==0 for r in metrics)
mesh=next(json.loads(p.read_text()) for p in (build/'hair_shape_final_dump').glob('*.mesh.json') if json.loads(p.read_text())['name']=='sx_mingyu_head_00')
assert mesh['name']=='sx_mingyu_head_00'
data=read(build/'hair_shape_final_dump'/f"sx_mingyu_head_{mesh['guid']}.bin");check_structure(data)
p=np.array(mesh['positions']);mapping=data['render_to_sim'];decoded=decode_positions(data)
assert np.linalg.norm(decoded[mapping]-p,axis=1).max()<.0002
assert np.allclose(data['bone_weights'].reshape(-1,4)[mapping]*255,mesh['weights'],atol=.0001)
assert np.array_equal(data['bone_indices'].reshape(-1,4)[mapping],mesh['bones'])
assert np.all(data['max_distances'][mapping]<=np.array(mesh['alpha'])/255+.000001)
candidate=build/'hair_shape_candidate_v1.1.5.tpac';previous=json.loads((ROOT/'reports/hair_clearance_validation.json').read_text())
module=ROOT/'module/ShengxiuCollection';xml=module/'ModuleData/cloth_bodies.xml'
assert sha(xml)==previous['collision_xml_sha256']
others={p.name:sha(p) for p in (module/'AssetPackages').glob('*.tpac') if p.name!='sx_mingyu.tpac'}
assert others==previous['other_set_package_hashes_unchanged']
packages=previous['packages']
for row in packages:
 if row['prefix']=='sx_mingyu':row['sha256']=sha(candidate);row['report']='reports/hair_shape_validation.json'
report={'status':'pass','version':'v1.1.5','final_package_sha256':sha(candidate),'baseline_package_sha256':previous['final_package_sha256'],'collision_xml_sha256':sha(xml),'check_scope':'actual_final_hair_geometry_and_native_skeletal_triangle_clearance','all_four_lods_checked':True,'hair_cloth_positions_weights_mapping_and_parallel_constraints_verified':True,'posterior_samples':'vertices, triangle centroids, three edge midpoints; original rear Y<-25mm and Z<1.50m','motions':rows,'other_set_package_hashes_unchanged':others,'packages':packages,'preservation':json.loads((ROOT/'reports/hair_shape_build.json').read_text()),'game_test_verified':False,'limitations':'Native skeletal poses and orthographic torso triangle rays do not run the game cloth solver, body sliders, weapon collision or IK. All available frames checked from frame 1 in idle/run/bow/riding. Rear travel is 12mm before quantization; front locks keep original distance.'}
(ROOT/'reports/hair_shape_validation.json').write_text(json.dumps(report,indent=2))
print('HAIR_SHAPE_OFFLINE_VERIFIED',sha(candidate),flush=True)
