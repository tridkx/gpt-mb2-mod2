"""CPU isolation of shipped distance/anchor passes; excludes engine collisions."""
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from cloth_payload import read,decode_positions
ROOT=Path(__file__).resolve().parents[1]
WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()))
anim=parse_animjson(json.loads((ROOT/'reports/idle.json').read_text()))
skin=skin_matrices(rig,anim,max(1,anim['start']))
rows=[]
native=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/ModuleData/cloth_bodies.xml')
body=next(b for b in ET.parse(native).getroot() if b.get('name')=='human_body')
bone_lookup={b['name']:b['i'] for b in json.loads((ROOT/'reports/human_skeleton.json').read_text())['bones']}
capsules=[]
for cap in body.findall('./capsules/capsule'):
 frame=np.fromstring(cap.get('frame'),sep=',').reshape(4,4)
 origin=np.fromstring(cap.get('origin'),sep=',')
 ends=[origin@frame[:3,:3]+frame[3,:3],(origin+np.array([float(cap.get('length')),0,0]))@frame[:3,:3]+frame[3,:3]]
 radii=[]
 for i,point in enumerate(cap.findall('./points/point')):
  bindings=[(bone_lookup[b.get('name')],float(b.get('weight'))) for b in point.findall('./bones/bone')]
  if sum(w for _,w in bindings)>0:
   ends[i]=sum(((skin[b,:3,:3]@ends[i]+skin[b,:3,3])*w for b,w in bindings))
  radii.append(float(point.get('radius')))
 capsules.append((cap.get('name'),*ends,*radii))
def collide(p):
 p=p.copy()
 for name,c0,c1,r0,r1 in capsules:
  axis=c1-c0;size=np.linalg.norm(axis);direction=axis/(size+.00001)
  projection=np.clip((p-c0)@direction,0,size);center=c0+projection[:,None]*direction
  radius=r0+(r1-r0)*projection/(size+.00001)
  delta=p-center;length=np.linalg.norm(delta,axis=1)
  p=center+delta*(np.maximum(length,radius)/np.maximum(length,1e-12))[:,None]
 return p
for plan in json.loads((ROOT/'build/cooked_cloth/manifest.json').read_text()):
 if plan['mesh'] not in ['sx_mingyu_head_00','sx_mingyu_body_06']:continue
 d=read(plan['path']); rest=decode_positions(d)
 target=lbs(rest,d['bone_indices'].reshape(-1,4),d['bone_weights'].reshape(-1,4)*255,skin)
 offset=collide(target)-target;active=d['max_distances']>0
 row={'mesh':plan['mesh'],'pass':'native_capsule_vertex_projection','active_vertices_inside':int((np.linalg.norm(offset[active],axis=1)>.0001).sum()),'max_lift_m':float(offset[active,2].max()),'max_displacement_m':float(np.linalg.norm(offset[active],axis=1).max()),'scope':'CPU capsule endpoint interpretation, idle frame; engine loading, body sliders and dummy collision excluded'}
 rows.append(row);print(row,flush=True)
 for immutable in [d['simulation_start'],d['normal_start']]:
  p=target.copy();prev=p.copy();c=d['constraints'];mov=(np.arange(len(p))>=immutable).astype(float)
  for step in range(240):
   nxt=p+(p-prev)*.48+np.array([0,0,-7/120**2]);prev=p.copy()
   delta=nxt-target;length=np.linalg.norm(delta,axis=1);p=target+delta*np.minimum(1,d['max_distances']/np.maximum(length,1e-12))[:,None]
   roots=d['anchors']>>16;limits=(d['anchors']&65535)*d['anchor_scale']
   delta=p-p[roots];length=np.linalg.norm(delta,axis=1)
   p-=delta*np.maximum(0,1-limits/np.maximum(length,1e-12))[:,None]
   for s in d['constraint_sets']:
    for k in [0,2]:
     start,count=s[k*2:k*2+2];ids=np.arange(start,start+count);a,b=c[ids].T
     delta=p[b]-p[a];length=np.linalg.norm(delta,axis=1)
     amount=delta*((1-d['rest_lengths'][ids]/np.maximum(length,1e-12))*(1 if k==0 else .35)/np.maximum(mov[a]+mov[b],1))[:,None]
     p[a]+=amount*mov[a,None];p[b]-=amount*mov[b,None]
  offset=p-target;active=d['max_distances']>0
  row={'mesh':plan['mesh'],'immutable_end':int(immutable),'max_lift_m':float(offset[active,2].max()),'p95_lift_m':float(np.quantile(offset[active,2],.95)),'max_displacement_m':float(np.linalg.norm(offset,axis=1).max()),'fixed_root_drift_m':float(np.linalg.norm(offset[:d['normal_start']],axis=1).max())}
  rows.append(row);print(row,flush=True)
(ROOT/'build/cloth_lift_diagnostic.json').write_text(json.dumps(rows,indent=2))
