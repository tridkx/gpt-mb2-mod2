"""Check protected skin/shorts triangle interiors against posed final proxies."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
from refit_skirt_collision import pose_capsule,clearance
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(workspace_root(R)/'tools/asset_helpers/previewer'))
from baker.animation import parse_animjson,skin_matrices
from baker.skeleton import parse_skeljson
def skin_points(p,w,skin):
 from baker.animation import lbs
 bi=np.argsort(-w,axis=1,kind='stable')[:,:4];ww=np.take_along_axis(w,bi,axis=1);ww/=ww.sum(1,keepdims=True);bw=np.floor(ww*255).astype(int);bw[:,0]+=255-bw.sum(1);return lbs(p,bi,bw,skin)
cfg=json.loads((R/'tools/model_config.json').read_text());data=np.load(R/'build/fitted_model.npz');manifest=json.loads((R/'build/manifest.json').read_text());transfer=json.loads((R/'reports/weight_transfer.json').read_text());names=transfer['native_bones'];j=np.array(transfer['source_landmarks']);meshes=[]
for rec in manifest:
 n=rec['object'];p=data[n+'_p'];w=data[n+'_w'];f=data[n+'_f'];score=w[:,[names.index('pelvis'),names.index('l_thigh'),names.index('r_thigh')]].sum(1)
 if 'body' in rec['material'].lower():
  keep=(score>.45)&(p[:,2]>min(j[names.index('l_calf'),2],j[names.index('r_calf'),2])-.03)&(p[:,2]<j[names.index('pelvis'),2]+.16)
 elif rec['material']==cfg['collision_refit'].get('shorts_guard',{}).get('material'):keep=np.ones(len(p),bool)
 else:continue
 faces=f[keep[f].all(1)];meshes.append((p,w,faces))
paint=json.loads((R/'reports/cloth_paint.json').read_text());alpha=np.load(R/'build/cloth_alphas.npz');rootps=[];rootws=[]
for row in paint['rows']:
 if not any(c['kind']=='skirt' for c in row['components']):continue
 n=row['object'];p=data[n+'_p'];w=data[n+'_w'];active=alpha[n]>0;height=max(c['bounds_m'][1][2] for c in row['components'] if c['kind']=='skirt')+.01;active&=p[:,2]<height;f=data[n+'_f'];e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ids=np.unique(np.concatenate([e[active[e[:,0]]&(alpha[n][e[:,1]]==0),1],e[active[e[:,1]]&(alpha[n][e[:,0]]==0),0]]));rootps.append(p[ids]);rootws.append(w[ids])
rootp=np.concatenate(rootps);rootw=np.concatenate(rootws)
rig=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((R/'build/skeleton_spec.json').read_text()))]});collision=json.loads((R/'reports/cloth_collision.json').read_text());caps=collision['capsules'];rows=[];fit='--fit' in sys.argv;original=np.array([c['radius_m'] for c in caps])
for label in ['idle','ui_neutral_female','run','bow','riding','slash']:
 anim=parse_animjson(json.loads((R/'reports'/(label+'.json')).read_text()));frames=sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,12).astype(int)));maximum=-100.;worst=0;total=0;outside=0;root_overlap=0.
 for frame in frames:
  skin=skin_matrices(rig,anim,frame);posed=[dict(c,endpoints_m=pose_capsule(c,skin,names).tolist()) for c in caps]
  root_overlap=max(root_overlap,float(np.maximum(-clearance(skin_points(rootp,rootw,skin),posed),0).max()))
  for p,w,f in meshes:
   tri=skin_points(p,w,skin)[f];points=np.concatenate([tri[:,0]*(i/4)+tri[:,1]*(k/4)+tri[:,2]*(1-(i+k)/4) for i in range(5) for k in range(5-i)]);gap=clearance(points,posed)
   if fit and (gap>0).any():
    distances=np.array([clearance(points,[c]) for c in posed]);near=distances.argmin(0)
    for index in np.unique(near[gap>0]):
     needed=float(gap[near==index].max())+.0001;caps[index]['radius_m']+=needed;posed[index]['radius_m']+=needed
    gap=clearance(points,posed)
   total+=len(gap);outside+=int((gap>1e-7).sum())
   if gap.max()>maximum:maximum=float(gap.max());worst=int(frame)
 rows.append(dict(fixed_root_max_overlap_m=root_overlap,pose=label,sampled_frames=len(frames),surface_samples=total,uncovered_samples=outside,maximum_outside_m=max(0,maximum),worst_frame=worst))
if fit:
 import xml.etree.ElementTree as ET
 collision['surface_fit_additions']=[dict(name=c['name'],added_radius_m=float(c['radius_m']-before)) for c,before in zip(caps,original) if c['radius_m']>before];assert max(c['radius_m']-before for c,before in zip(caps,original))<.002
 (R/'reports/cloth_collision.json').write_text(json.dumps(collision,indent=2));path=R/'module'/cfg['id']/'ModuleData/cloth_bodies.xml';tree=ET.parse(path)
 for node in tree.findall('.//capsule'):
  cap=next(c for c in caps if cfg['prefix']+'_'+c['name']==node.get('name'))
  for point in node.findall('./points/point'):point.set('radius',f"{cap['radius_m']:.6f}")
 tree.write(path,encoding='utf8',xml_declaration=True)
report=dict(status='pass' if all(r['uncovered_samples']==0 and r['fixed_root_max_overlap_m']<=cfg['skirt_proxy_limits']['sampled_pose_fixed_root_overlap_m'] for r in rows) else 'fail',version=cfg['version'],rows=rows,sampling='12 non-bind frames per Native motion, actual skinned triangle vertices/edges/interiors with barycentric subdivisions 4; full decoded vertex cycles scanned by collision fitter',game_verified=False)
(R/'reports/skirt_surface_coverage.json').write_text(json.dumps(report,indent=2));print(report)
assert report['status']=='pass','Protected surface outside capsule union'
