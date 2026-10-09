"""Quantify requested corrections and verify preserved rig/cloth inputs."""
from pathlib import Path
import numpy as np,json,hashlib,sys,subprocess
ROOT=Path(__file__).resolve().parents[1];WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'))
from georead import read_geo
from proportion_fit import apply_proportions
cfg=json.loads((ROOT/'tools/model_config.json').read_text())['proportion_repair']
old=np.load(ROOT/'build/proportion_baseline_v1.0.0/rig_arrays.npz');new=np.load(ROOT/'build/rig_arrays.npz')
assert np.array_equal(old['world'],new['world'])
records=json.loads((ROOT/'build/rig_manifest.json').read_text());unchanged=[]
for rec in records:
 n=rec['object']
 for field in ['S','W','A']:assert np.array_equal(old[n+'_'+field],new[n+'_'+field]),(n,field)
 expected=apply_proportions(old[n+'_P'],cfg,rec['part'],old[n+'_S'])
 assert np.max(abs(expected-new[n+'_P']))<1e-12
 if np.array_equal(old[n+'_P'],new[n+'_P']):unchanged.append(n)
head='sx_mingyu_head_08';skull=old[head+'_P'][:,2]>1.57
width_old=np.ptp(old[head+'_P'][skull,0]);width_new=np.ptp(new[head+'_P'][skull,0])
assert abs(width_new/width_old-1.10)<1e-9
shoes='sx_mingyu_legs_05';sole=old[shoes+'_S'][:,2]<.005
o=old[shoes+'_P'][sole];p=new[shoes+'_P'][sole]
assert abs(p[:,2].min()-.001)<1e-9
assert p[:,2].max()<.00101
old_slope=np.polyfit(o[:,1],o[:,2],1)[0];slope=np.polyfit(p[:,1],p[:,2],1)[0]
assert abs(slope)<.01
foot=sole
old_length=np.ptp(old[shoes+'_P'][foot,1]);length=np.ptp(new[shoes+'_P'][foot,1])
assert length/old_length<.90
package=ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tool=str(WS/'tools/AssetTool/AssetTool.dll')
before=json.loads(subprocess.check_output(['dotnet',tool,'inspect',str(ROOT/'build/proportion_baseline_v1.0.0/sx_mingyu.tpac')],text=True))
after=json.loads(subprocess.check_output(['dotnet',tool,'inspect',str(package)],text=True))
assert before==after,'cloth settings or runtime metadata changed'
# Final LOD0 positions must be the repaired editable geometry (UV/normal splits allowed).
from scipy.spatial import cKDTree
for file in (ROOT/'build/final_export/geo').glob('*.bin'):
 for m in read_geo(file):
  assert cKDTree(new[m['name']+'_P']).query(m['pos'])[0].max()<2e-6
report={'status':'pass','version':'v1.0.1','final_package_sha256':sha(package),'baseline_package_sha256':sha(ROOT/'build/proportion_baseline_v1.0.0/sx_mingyu.tpac'),
 'head_width_ratio':width_new/width_old,'neck_backward_m':cfg['neck_backward_m'],'foot_pitch_correction_degrees':cfg['foot_pitch_degrees'],
 'foot_length_m_before':old_length,'foot_length_m_after':length,'foot_length_ratio':length/old_length,
 'sole_height_range_m_before':[float(o[:,2].min()),float(o[:,2].max())],'sole_height_range_m_after':[float(p[:,2].min()),float(p[:,2].max())],
 'sole_slope_before':old_slope,'sole_slope_after':slope,'native_skeleton_unchanged':True,'weights_unchanged':True,'cloth_alpha_unchanged':True,'all_runtime_cloth_metadata_unchanged':True,
 'unchanged_meshes':unchanged,'game_test_verified':False,'ground_scope':'bind pose geometry vs z=0 plane; native motion checked separately; in-game ground/IK needs user testing'}
(ROOT/'reports/proportion_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
