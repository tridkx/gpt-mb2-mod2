"""Posterior hair versus actual torso triangles, in spine2 rest coordinates."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parents[1]
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'))
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def change(p):
 # Keep scalp, front locks and attachments; taper along the rear neck.
 rear=1-smooth(-.025,.015,p[:,1]);lower=1-smooth(1.46,1.61,p[:,2])
 factor=rear*lower
 q=p.copy();q[:,1]-=.75*np.maximum(p[:,1]+.22,0)*factor
 return q,rear*(1-smooth(1.40,1.57,p[:,2]))*.98

def rear_surface(points,tri):
 # Orthographic ray/triangle intersection along Y. Min Y is the back surface.
 a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a
 det=b[:,0]*c[:,2]-b[:,2]*c[:,0];ok=abs(det)>1e-10
 a=a[ok];b=b[ok];c=c[ok];det=det[ok]
 # Exact broad phase: each 2cm cell contains every triangle whose XZ bounds
 # overlap it. This avoids testing each hair sample against the entire torso.
 size=.02;grid={};cells=np.floor(points[:,[0,2]]/size).astype(int)
 bounds=np.stack([a,a+b,a+c]);low=np.floor(bounds[:,:,[0,2]].min(0)/size).astype(int);high=np.floor(bounds[:,:,[0,2]].max(0)/size).astype(int)
 for i,(lo,hi) in enumerate(zip(low,high)):
  for x in range(lo[0],hi[0]+1):
   for z in range(lo[1],hi[1]+1):grid.setdefault((x,z),[]).append(i)
 result=np.full(len(points),np.inf)
 for cell in np.unique(cells,axis=0):
  ids=np.flatnonzero(np.all(cells==cell,axis=1));ts=grid.get(tuple(cell),[])
  if not ts:continue
  aa=a[ts];bb=b[ts];cc=c[ts];dd=det[ts];chunk=points[ids]
  dx=chunk[:,None,0]-aa[None,:,0];dz=chunk[:,None,2]-aa[None,:,2]
  u=(dx*cc[:,2]-dz*cc[:,0])/dd;v=(bb[:,0]*dz-bb[:,2]*dx)/dd
  y=aa[:,1]+u*bb[:,1]+v*cc[:,1]
  y[(u<-.00001)|(v<-.00001)|(u+v>1.00001)]=np.inf
  result[ids]=y.min(1)
 return result

def evaluate(meshes,changed=False,posterior_mask=None,sample_faces=False,full_cycles=False):
 hair=next(m for m in meshes if m['name']=='sx_mingyu_head_00')
 p=hair['pos'];mask=(p[:,1]<-.025)&(p[:,2]<1.50)
 if posterior_mask is not None:mask=posterior_mask
 if changed:
  p,t=change(p);bi=np.column_stack([np.full(len(p),13),np.full(len(p),11),np.zeros((len(p),2),int)])
  w=np.zeros((len(p),4));w[:,1]=np.round(t*255);w[:,0]=255-w[:,1]
 else:bi=hair['bi'];w=hair['bw']
 garments=[]
 for m in meshes:
  if m['name'] not in ['sx_mingyu_body_01','sx_mingyu_body_02','sx_mingyu_body_13','sx_mingyu_body_06']:continue
  f=m['idx'].reshape(-1,3);v=m['pos'][f]
  keep=(abs(v[:,:,0]).max(1)<.18)&(v[:,:,1].min(1)>-.18)&(v[:,:,2].min(1)>.90)
  garments.append((m,f[keep]))
 rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));rows=[]
 for label in ['rest','idle','run','bow','riding']:
  anim=None if label=='rest' else parse_animjson(json.loads((ROOT/f'reports/{label}.json').read_text()))
  frames=[0] if anim is None else range(max(1,anim['start']),anim['frames'])
  if label in ['idle','bow'] and not full_cycles:frames=np.linspace(max(1,anim['start']),anim['frames']-1,16,dtype=int)
  for frame in frames:
   skin=np.repeat(np.eye(4)[None],28,axis=0) if anim is None else skin_matrices(rig,anim,int(frame))
   inv=np.linalg.inv(skin[11]);hp=lbs(p,bi,w,skin);hp=hp@inv[:3,:3].T+inv[:3,3]
   triangles=[]
   for m,f in garments:
    gp=lbs(m['pos'],m['bi'],m['bw'],skin);gp=gp@inv[:3,:3].T+inv[:3,3];triangles.append(gp[f])
   samples=hp[mask]
   if sample_faces:
    faces=hair['idx'].reshape(-1,3);faces=faces[np.all(mask[faces],axis=1)]
    tri=hp[faces]
    samples=np.concatenate([samples,tri.mean(1),(tri[:,0]+tri[:,1])/2,(tri[:,1]+tri[:,2])/2,(tri[:,2]+tri[:,0])/2])
   surface=rear_surface(samples,np.concatenate(triangles));hit=np.isfinite(surface)
   margin=surface[hit]-samples[hit,1]
   rows.append(dict(animation=label,frame=int(frame),covered_vertices=int(hit.sum()),inside_vertices=int((margin<0).sum()),minimum_gap_m=float(margin.min()) if len(margin) else None))
 return rows

if __name__=='__main__':
 meshes=[m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f)]
 before=evaluate(meshes);after=evaluate(meshes,True)
 report={'scope':'skeletal ray to actual torso triangles; excludes cloth physics and body sliders','before':before,'proposed':after}
 (ROOT/'reports/hair_shape_diagnosis.json').write_text(json.dumps(report,indent=2))
 for label in ['rest','idle','run','bow','riding']:
  print(label,[(tag,min(r['minimum_gap_m'] for r in rows if r['animation']==label),max(r['inside_vertices'] for r in rows if r['animation']==label)) for tag,rows in [('before',before),('proposed',after)]])
