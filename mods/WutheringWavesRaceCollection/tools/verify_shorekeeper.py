"""Check final arm weights and the whole creation idle against the accepted baseline."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.spatial import cKDTree
S=Path(__file__).resolve().parents[1];R=S/'ShorekeeperRace'
W=next(p for p in S.parents if (p/'tools/asset_helpers').is_dir())
sys.path[:0]=[str(W/'tools/asset_helpers/tools'),str(W/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
def load(folder):return next(m for p in (folder/'geo').glob('*.bin') for m in read_geo(p) if m['name']=='ww_shorekeeper_part_00')
def main():
 old=load(R/'build/previous_v0.1.0_export');new=load(R/'build/final_export_lod0')
 for key in ['pos','uv']:
  a=np.column_stack([old['pos'],old['uv']]);b=np.column_stack([new['pos'],new['uv']]);assert cKDTree(a).query(b)[0].max()<3e-6 and cKDTree(b).query(a)[0].max()<3e-6
 rig=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
 mask=(abs(new['pos'][:,0])>.25)&(new['pos'][:,2]>1)
 arm_influence=sum((new['bw'][:,i]/255)*np.isin(new['bi'][:,i],np.arange(14,28)) for i in range(4))
 assert np.mean(arm_influence[mask])>.85
 oldmask=(abs(old['pos'][:,0])>.25)&(old['pos'][:,2]>1)
 motions={}
 for label,path in [('female','facegen.json'),('male','creation_male.json')]:
  anim=parse_animjson(json.loads((R/'reports'/path).read_text()));frames=range(max(1,anim['start']),anim['frames']);samples=[]
  for frame in frames:
   skin=skin_matrices(rig,anim,frame);a=lbs(old['pos'][oldmask],old['bi'][oldmask],old['bw'][oldmask],skin);b=lbs(new['pos'][mask],new['bi'][mask],new['bw'][mask],skin)
   samples.append({'frame':frame,'old_arm_horizontal_extent_mean_m':float(np.mean(abs(a[:,0]))),'new_arm_horizontal_extent_mean_m':float(np.mean(abs(b[:,0]))),'old_arm_height_mean_m':float(a[:,2].mean()),'new_arm_height_mean_m':float(b[:,2].mean())})
  assert all(s['new_arm_horizontal_extent_mean_m']<s['old_arm_horizontal_extent_mean_m']*.8 for s in samples),label
  motions[label]={'animation':anim['name'],'frames_checked':len(samples),'samples':samples}
 package=R/'module/ShorekeeperRace/AssetPackages/ww_shorekeeper.tpac'
 report={'status':'pass','version':'v0.1.1','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'cause':'Mixed MI_Down material contained arms; whole-material skirt weights removed arm influences','fix':'Keep material 0 source body/arm skinning and smooth the weight field; only separate skirt materials receive skirt weights','source_positions_and_uv_unchanged':True,'material_0_arm_vertex_count':int(mask.sum()),'mean_native_arm_influence':float(arm_influence[mask].mean()),'creation_idle_motions':motions,'game_verified':False,'limitations':['Offline idle and mesh proof do not replace creation-page live retest']}
 (R/'reports/creation_arm_validation.json').write_text(json.dumps(report,indent=2));print('CREATION_ARM_VERIFIED',[(k,v['frames_checked']) for k,v in motions.items()],'frames, native arm influence',report['mean_native_arm_influence'])
if __name__=='__main__':main()
