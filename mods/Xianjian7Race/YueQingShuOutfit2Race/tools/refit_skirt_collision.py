"""Fit each thigh from its own anatomical surface, with a local shorts guard."""
import numpy as np

def samples(p,f,w,divisions=4):
 positions=[];weights=[];tri=p[f];tw=w[f]
 for i in range(divisions+1):
  for j in range(divisions+1-i):
   a=i/divisions;b=j/divisions;c=1-a-b
   positions.append(tri[:,0]*a+tri[:,1]*b+tri[:,2]*c)
   weights.append(tw[:,0]*a+tw[:,1]*b+tw[:,2]*c)
 return np.concatenate(positions),np.concatenate(weights)

def clearance(p,caps):
 out=np.full(len(p),100.)
 for cap in caps:
  a,b=np.array(cap['endpoints_m']);v=b-a;t=np.clip((p-a)@v/max(v@v,1e-12),0,1)
  out=np.minimum(out,np.linalg.norm(p-a-t[:,None]*v,axis=1)-cap['radius_m'])
 return out

def binding(weights,names):
 mean=weights.mean(0);ids=np.argsort(-mean)[:2];values=mean[ids];values/=values.sum()
 return [dict(bone=names[int(i)],weight=float(v)) for i,v in zip(ids,values) if v>1e-7]

def pose_capsule(cap,skin,names):
 out=[]
 for i,(point,bone) in enumerate(zip(cap['endpoints_m'],cap['bones'])):
  weights=cap.get('endpoint_weights',[[dict(bone=b,weight=1.)] for b in cap['bones']])[i]
  q=np.zeros(3)
  for influence in weights:
   matrix=skin[names.index(influence['bone'])];q+=influence['weight']*(matrix[:3,:3]@point+matrix[:3,3])
  out.append(q)
 return np.array(out)

def fit(caps,data,manifest,transfer,cfg,root=None):
 names=transfer['native_bones'];rows=[];ps=[];ws=[]
 for rec in manifest:
  if 'body' not in rec['material'].lower():continue
  n=rec['object'];p,w=samples(data[n+'_p'],data[n+'_f'],data[n+'_w']);ps.append(p);ws.append(w)
 p=np.concatenate(ps);w=np.concatenate(ws)
 for cap in caps:
  if cap['name'] not in ['l_thigh','r_thigh']:continue
  pre=cap['name'][0];a,b=np.array(cap['endpoints_m']);v=b-a;t=(p-a)@v/(v@v)
  owned=w[:,[names.index(pre+'_thigh'),names.index(pre+'_calf'),names.index('pelvis')]].sum(1)
  keep=(p[:,0]*(-1 if pre=='l' else 1)>0)&(t>=0)&(t<=1)&(owned>.8)
  q=p[keep];assert len(q)>100
  distances=np.linalg.norm(q-a-t[keep,None]*v,axis=1)
  old=cap['radius_m'];cap['radius_m']=float(distances.max()+cfg['collision_refit']['skin_clearance_m'])
  owned_weights=w[keep];tau=t[keep]
  cap['endpoint_weights']=[binding(owned_weights[tau<=np.quantile(tau,.12)],names),binding(owned_weights[tau>=np.quantile(tau,.88)],names)]
  rows.append(dict(name=cap['name'],sample_points=len(q),maximum_skin_distance_m=float(distances.max()),baseline_radius_m=float(old),radius_m=cap['radius_m'],same_side_and_anatomical_filter=True))
 guard=cfg['collision_refit'].get('shorts_guard')
 guard_points=[]
 if not guard:
  joints=np.array(transfer['source_landmarks']);pelvis=joints[names.index('pelvis')];width=abs(joints[names.index('l_thigh'),0]-joints[names.index('r_thigh'),0])
  score=w[:,[names.index('pelvis'),names.index('l_thigh'),names.index('r_thigh')]].sum(1)
  keep=(score>.45)&(p[:,2]>pelvis[2]-.12)&(p[:,2]<pelvis[2]+.16)&(abs(p[:,0])<width*1.1);hip=p[keep];hw=w[keep];xs=np.array([-width*.3,0,width*.3]);assigned=abs(hip[:,0,None]-xs).argmin(1)
  for index,cap in enumerate(c for c in caps if c['name'].startswith('pelvis_')):
   q=hip[assigned==index];qw=hw[assigned==index];cy=float((q[:,1].min()+q[:,1].max())/2);lo=float(q[:,2].min()+.02);hi=float(q[:,2].max()-.02)
   if hi<=lo:lo=float(q[:,2].mean()-.0005);hi=lo+.001
   a=np.array([xs[index],cy,lo]);b=np.array([xs[index],cy,hi]);v=b-a;t=np.clip((q-a)@v/(v@v),0,1)
   cap['endpoints_m']=[a.tolist(),b.tolist()];cap['radius_m']=float(np.linalg.norm(q-a-t[:,None]*v,axis=1).max()+.001)
   cap['endpoint_weights']=[binding(qw[q[:,2]<=np.quantile(q[:,2],.25)],names),binding(qw[q[:,2]>=np.quantile(q[:,2],.75)],names)]
 if guard:
  rec=next(r for r in manifest if r['material']==guard['material']);n=rec['object'];points,weights=samples(data[n+'_p'],data[n+'_f'],data[n+'_w']);guard_points=points
  if guard.get('include_pelvis_skin'):
   keep=w[:,names.index('pelvis')]>.5
   points=np.concatenate([points,p[keep]]);weights=np.concatenate([weights,w[keep]]);guard_points=points
  # Short capsules along the depth axis follow the actual shorts in small
  # height/width bands. This avoids a tall capsule's oversized upper end cap.
  caps[:]=[c for c in caps if not c['name'].startswith('pelvis_')]
  root_poses=[];skins=[];adaptive_stats=dict(split_cells=0,minimum_root_clearance_m=100.)
  if guard.get('respect_skirt_roots'):
   import sys,json
   from workspace_paths import workspace_root
   sys.path.insert(0,str(workspace_root(root)/'tools/asset_helpers/previewer'))
   from baker.skeleton import parse_skeljson
   from baker.animation import parse_animjson,skin_matrices,lbs
   rp,rw=skirt_root_arrays(data,root);rig=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((root/'build/skeleton_spec.json').read_text()))]})
   for label in ['ui_neutral_female','run','bow','riding','slash']:
    anim=parse_animjson(json.loads((root/'reports'/(label+'.json')).read_text()));frames=range(max(1,anim['start']),anim['frames']) if label=='run' else sorted(set(np.linspace(max(1,anim['start']),anim['frames']-1,12).astype(int)))
    for frame in frames:
     skin=skin_matrices(rig,anim,frame);skins.append(skin);root_poses.append(skin_points(rp,rw,skin))
  def create_guard(q,qw,label,depth=0):
   cx=float((q[:,0].min()+q[:,0].max())/2);cz=float((q[:,2].min()+q[:,2].max())/2);span=float(np.ptp(q[:,1]));trim=min(span*.10,guard.get('depth_end_trim_m',.025));cy=float((q[:,1].min()+q[:,1].max())/2)
   a=np.array([cx,min(q[:,1].min()+trim,cy-.0005),cz]);b=np.array([cx,max(q[:,1].max()-trim,cy+.0005),cz]);v=b-a;t=np.clip((q-a)@v/(v@v),0,1);radius=float(np.linalg.norm(q-a-t[:,None]*v,axis=1).max()+guard['clearance_m'])
   bind_a=binding(qw[q[:,1]<=np.quantile(q[:,1],.25)],names);bind_b=binding(qw[q[:,1]>=np.quantile(q[:,1],.75)],names)
   candidate=dict(name=label,endpoints_m=[a.tolist(),b.tolist()],radius_m=radius,bones=[bind_a[0]['bone'],bind_b[0]['bone']],endpoint_weights=[bind_a,bind_b]);available=100.
   for skin,rp in zip(skins,root_poses):
    aa,bb=pose_capsule(candidate,skin,names);axis=bb-aa;t=np.clip((rp-aa)@axis/max(axis@axis,1e-12),0,1);available=min(available,float(np.linalg.norm(rp-aa-t[:,None]*axis,axis=1).min())--guard.get('maximum_fixed_root_overlap_m',0.))
    qp=skin_points(q,qw,skin);t=np.clip((qp-aa)@axis/max(axis@axis,1e-12),0,1);radius=max(radius,float(np.linalg.norm(qp-aa-t[:,None]*axis,axis=1).max())+guard['clearance_m'])
   if radius>available:
    spans=np.ptp(q,axis=0);axis=0 if spans[0]>=spans[2] else 2
    if spans[axis]<.003:axis=int(spans.argmax())
    assert depth<18 and spans[axis]>.00001,('Body/root fitting infeasible',label,radius,available,q.min(0),q.max(0))
    mid=(q[:,axis].min()+q[:,axis].max())/2;left=q[:,axis]<=mid;assert left.any() and (~left).any()
    adaptive_stats['split_cells']+=1;create_guard(q[left],qw[left],label+'a',depth+1);create_guard(q[~left],qw[~left],label+'b',depth+1);return
   candidate['radius_m']=radius;adaptive_stats['minimum_root_clearance_m']=min(adaptive_stats['minimum_root_clearance_m'],available+-guard.get('maximum_fixed_root_overlap_m',0.)-radius);caps.append(candidate)
   assert sum(c['name'].startswith('shorts_') for c in caps)<=256,'Too many adaptive collision cells'
  zz=np.linspace(points[:,2].min(),points[:,2].max(),guard['height_bands']+1)
  for iz in range(guard['height_bands']):
   columns=guard.get('top_columns',guard['columns']) if iz==guard['height_bands']-1 else guard['columns']
   xx=np.linspace(points[:,0].min(),points[:,0].max(),columns+1)
   for ix in range(columns):
    keep=(points[:,0]>=xx[ix])&(points[:,0]<=xx[ix+1])&(points[:,2]>=zz[iz])&(points[:,2]<=zz[iz+1]);q=points[keep];qw=weights[keep]
    if not len(q):continue
    create_guard(q,qw,f'shorts_{ix}_{iz}')
 return dict(adaptive_guard=adaptive_stats if guard else None,thighs=rows,shorts_guard_capsules=sum(c['name'].startswith('shorts_') for c in caps),shorts_surface_samples=len(guard_points),sampling='Triangle vertices, edges and interiors at barycentric subdivisions=4',source_geometry_weights_alpha_changed=False)

def fit_waist_roots(caps,data,manifest,transfer,cfg,root):
 """Keep the covered-waist proxy clear of real hanging-panel root vertices."""
 import sys,json
 from workspace_paths import workspace_root
 sys.path.insert(0,str(workspace_root(root)/'tools/asset_helpers/previewer'))
 from baker.skeleton import parse_skeljson
 from baker.animation import parse_animjson,skin_matrices,lbs
 paint=json.loads((root/'reports/cloth_paint.json').read_text());alpha=np.load(root/'build/cloth_alphas.npz');ps=[];ws=[]
 for row in paint['rows']:
  if not any(c['kind']=='skirt' for c in row['components']):continue
  n=row['object'];p=data[n+'_p'];w=data[n+'_w'];active=alpha[n]>0;height=max(c['bounds_m'][1][2] for c in row['components'] if c['kind']=='skirt')+.01;active&=p[:,2]<height;f=data[n+'_f'];e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ids=np.unique(np.concatenate([e[active[e[:,0]]&(alpha[n][e[:,1]]==0),1],e[active[e[:,1]]&(alpha[n][e[:,0]]==0),0]]));ps.append(p[ids]);ws.append(w[ids])
 p=np.concatenate(ps);w=np.concatenate(ws).astype(float);bi=np.argsort(-w,axis=1,kind='stable')[:,:4];ww=np.take_along_axis(w,bi,axis=1);ww/=ww.sum(1,keepdims=True);bw=np.floor(ww*255).astype(int);bw[:,0]+=255-bw.sum(1)
 rig=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((root/'build/skeleton_spec.json').read_text()))]});cap=next(c for c in caps if c['name']=='waist');minimum=100.
 for label in ['idle','ui_neutral_female','run','bow','riding','slash']:
  anim=parse_animjson(json.loads((root/'reports'/(label+'.json')).read_text()))
  for frame in range(max(1,anim['start']),anim['frames']):
   skin=skin_matrices(rig,anim,frame);q=lbs(p,bi,bw,skin);a,b=pose_capsule(cap,skin,rig['names']);v=b-a;t=np.clip((q-a)@v/max(v@v,1e-12),0,1);minimum=min(minimum,float(np.linalg.norm(q-a-t[:,None]*v,axis=1).min()))
 old=cap['radius_m'];cap['radius_m']=min(old,minimum-.001);assert cap['radius_m']>.012,('Waist proxy cannot fit roots',minimum)
 return dict(root_vertices=len(p),waist_radius_before_m=old,waist_radius_m=cap['radius_m'],minimum_root_axis_distance_m=minimum,full_decoded_cycles=True,covered_waist_is_proxy=True)

def skin_points(p,w,skin):
 from baker.animation import lbs
 w=w.astype(float);bi=np.argsort(-w,axis=1,kind='stable')[:,:4];ww=np.take_along_axis(w,bi,axis=1);ww/=ww.sum(1,keepdims=True);bw=np.floor(ww*255).astype(int);bw[:,0]+=255-bw.sum(1)
 return lbs(p,bi,bw,skin)

def skirt_root_arrays(data,root):
 import json
 paint=json.loads((root/'reports/cloth_paint.json').read_text());alpha=np.load(root/'build/cloth_alphas.npz');ps=[];ws=[]
 for row in paint['rows']:
  if not any(c['kind']=='skirt' for c in row['components']):continue
  n=row['object'];p=data[n+'_p'];w=data[n+'_w'];active=alpha[n]>0;height=max(c['bounds_m'][1][2] for c in row['components'] if c['kind']=='skirt')+.01;active&=p[:,2]<height;f=data[n+'_f'];e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ids=np.unique(np.concatenate([e[active[e[:,0]]&(alpha[n][e[:,1]]==0),1],e[active[e[:,1]]&(alpha[n][e[:,0]]==0),0]]));ps.append(p[ids]);ws.append(w[ids])
 return np.concatenate(ps),np.concatenate(ws)

def fit_pose_envelope(caps,data,manifest,transfer,cfg,root):
 """Add only measured own-body clearance, scanning full Native cycles."""
 import sys,json
 from workspace_paths import workspace_root
 sys.path.insert(0,str(workspace_root(root)/'tools/asset_helpers/previewer'))
 from baker.skeleton import parse_skeljson
 from baker.animation import parse_animjson,skin_matrices,lbs
 names=transfer['native_bones'];j=np.array(transfer['source_landmarks']);ps=[];ws=[]
 for rec in manifest:
  n=rec['object'];p=data[n+'_p'];w=data[n+'_w'];score=w[:,[names.index('pelvis'),names.index('l_thigh'),names.index('r_thigh')]].sum(1)
  if 'body' in rec['material'].lower():
   keep=(score>.45)&(p[:,2]>min(j[names.index('l_calf'),2],j[names.index('r_calf'),2])-.03)&(p[:,2]<j[names.index('pelvis'),2]+.16)
  elif rec['material']==cfg['collision_refit'].get('shorts_guard',{}).get('material'):keep=np.ones(len(p),bool)
  else:continue
  ps.append(p[keep]);ws.append(w[keep])
 p=np.concatenate(ps);w=np.concatenate(ws).astype(float);bi=np.argsort(-w,axis=1,kind='stable')[:,:4];ww=np.take_along_axis(w,bi,axis=1);ww/=ww.sum(1,keepdims=True);bw=np.floor(ww*255).astype(int);bw[:,0]+=255-bw.sum(1)
 rig=parse_skeljson({'bones':[dict(i=i,**b) for i,b in enumerate(json.loads((root/'build/skeleton_spec.json').read_text()))]})
 original=np.array([c['radius_m'] for c in caps]);changed=set();poses=[];maximum=0.
 for label in ['idle','ui_neutral_female','run','bow','riding','slash']:
  anim=parse_animjson(json.loads((root/'reports'/(label+'.json')).read_text()));frames=range(max(1,anim['start']),anim['frames'])
  for frame in frames:
   skin=skin_matrices(rig,anim,frame);q=lbs(p,bi,bw,skin);distances=[]
   for c in caps:
    a,b=pose_capsule(c,skin,names);v=b-a;t=np.clip((q-a)@v/max(v@v,1e-12),0,1);distances.append(np.linalg.norm(q-a-t[:,None]*v,axis=1)-c['radius_m'])
   distances=np.array(distances);nearest=distances.argmin(0);gap=distances.min(0);maximum=max(maximum,float(gap.max()))
   for index in np.unique(nearest[gap>0]):
    c=caps[index];assert c['name'].endswith(('thigh','calf')) or c['name'].startswith(('pelvis_','shorts_')),('Unexpected body fitting region',label,frame,c['name'])
    needed=float(gap[nearest==index].max())+.001;c['radius_m']+=needed;changed.add(int(index))
  poses.append(dict(pose=label,frames_checked=len(frames),sampling='Every decoded non-bind frame, protected source vertices'))
 additions=np.array([c['radius_m'] for c in caps])-original
 assert additions.max()<.025,('Dynamic body margin too large; revisit bindings',additions.max())
 return dict(protected_vertices=len(p),full_cycles=poses,maximum_initial_body_outside_m=maximum,changes=[dict(name=caps[i]['name'],added_radius_m=float(additions[i]),radius_m=caps[i]['radius_m']) for i in sorted(changed)],scope='Own hip/thigh skin and configured shorts vertex envelope; detailed surface coverage is checked separately')
