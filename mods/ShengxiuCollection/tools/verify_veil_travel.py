"""Native weapon poses test available travel, not cloth dynamics."""
from pathlib import Path
import sys,json,hashlib,numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
plan=json.loads((ROOT/'reports/veil_distance_plan.json').read_text())
arrays=np.load(ROOT/'build/rig_arrays.npz');old=np.load(ROOT/'build/cloth_baseline_v1.0.1/rig_arrays.npz')
stream=np.load(ROOT/'build/final_sleeve_channels.npz');points=stream['positions'];tree=cKDTree(points)
lod1=np.load(ROOT/'build/final_sleeve_channels_lod1.npz');lod1tree=cKDTree(lod1['positions'])
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
panels=[]
for panel in plan['panels']:
 name=panel['mesh'];ids=np.array(panel['vertices']);roots=np.array(panel['fixed_vertices'])
 dist,final_ids=tree.query(arrays[name+'_P'][ids]);assert dist.max()<2e-6
 assert np.all(stream['bone_indices'][final_ids,0]==panel['bone']) and np.all(stream['bone_weights'][final_ids,0]==255)
 root_points=arrays[name+'_P'][roots];_,nearest=cKDTree(root_points).query(points[final_ids]);anchor=root_points[nearest]
 dist,root_indices=lod1tree.query(root_points);assert dist.max()<2e-6
 assert np.all(lod1['colors'][root_indices,3]==0),'LOD1 lost fixed cuff anchors'
 root_distance=np.linalg.norm(points[final_ids]-anchor,axis=1)
 alpha=stream['colors'][final_ids,3]/255
 scale=plan['settings']['reader_unknown_float1']
 # 2*lever length bounds distance between any two orientations of a rigid
 # offset around the same cuff. Quantisation tolerance is explicitly kept.
 assert np.all(2*root_distance<=alpha*scale+scale/255+3e-6)
 panels.append((panel,final_ids,anchor,root_distance,alpha,old[name+'_A'][ids]))
motions=[]
for label in ['weapon_slash','bow']:
 raw=json.loads((ROOT/'reports'/(label+'.json')).read_text());anim=parse_animjson(raw)
 assert raw['skeletonGuid']==rig['guid'] and anim['have'].all() and anim['frames']>2
 total=blocked_before=blocked_after=0;max_required=0;worst_frame=1
 for frame in range(max(1,anim['start']),anim['frames']):
  skin=skin_matrices(rig,anim,frame)
  for panel,ids,anchors,length,alpha,before in panels:
   posed=lbs(points[ids],stream['bone_indices'][ids],stream['bone_weights'][ids],skin)
   bone=panel['bone'];moving_anchors=anchors@skin[bone,:3,:3].T+skin[bone,:3,3]
   # Vertical target is a travel-feasibility probe. It is not a solved sheet.
   hanging=moving_anchors.copy();hanging[:,2]-=length
   required=np.linalg.norm(hanging-posed,axis=1);free=length>.005
   total+=int(free.sum());blocked_before+=int((free&(required>before+1/255)).sum())
   blocked_after+=int((free&(required>alpha*scale+scale/255)).sum())
   if float(required.max())>max_required:max_required=float(required.max());worst_frame=frame
 assert blocked_after==0
 motions.append({'label':label,'asset':raw['name'],'frames_checked':int(anim['frames']-max(1,anim['start'])),
  'sample_count':total,'old_insufficient_samples':blocked_before,'candidate_insufficient_samples':blocked_after,
  'largest_required_travel_m':max_required,'largest_travel_frame':int(worst_frame)})
package=ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
report={'status':'pass','version':'v1.0.3','final_package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
 'method':'Final TPAC byte-alpha and weights, current native weapon/bow rotations, vertical travel feasibility and 2*lever bound',
 'assumption':'UnknownFloat1=3 acts as alpha-distance scale. This mapping is inferred and requires game verification.',
 'game_solver_verified':False,'motions':motions,'panels':[{'vertices':len(p['vertices']),'fixed_vertices':len(p['fixed_vertices']),
 'path_length_max_m':p['max_path_m'],'alpha_max':max(p['painted_alpha'])} for p in plan['panels']]}
(ROOT/'reports/veil_travel_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
