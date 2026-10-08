"""Offline pose-envelope fitting of skirt anchors, with triangle interior samples.
No game solver. Stores a reproducible per-vertex correction, never hides legs.
"""
import sys,json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[1];BASE=ROOT/'build/repair_baseline_v1.0.0'
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'));sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from subprocess import run
baselinegeo=BASE/'export/geo'
if not baselinegeo.exists():
    config=json.loads((ROOT/'mod.json').read_text());run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(BASE/config['package']),str(BASE/'export'),'0'],check=True,capture_output=True)

from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,pose
a=np.load(BASE/'rig_arrays.npz');fit=json.loads((BASE/'reports/rig_fit.json').read_text());name=next(r['object'] for r in fit['parts'] if r['kind']=='skirt')
m=next(m for f in (BASE/'export/geo').glob('*.bin') for m in read_geo(f) if m['name']==name)
# Consolidate final UV seams onto editable source vertex indices.
_,ids=cKDTree(a[name+'_P']).query(m['pos']);tri=ids[m['idx'].reshape(-1,3)];p=a[name+'_P'].copy();src=a[name+'_S'];n=len(p)
tri=np.array(json.loads((ROOT/'build/skirt_triangles.json').read_text()))
def smooth(lo,hi,x):t=np.clip((x-lo)/(hi-lo),0,1);return t*t*(3-2*t)
width=.14;knee=.58;waist=.98
r=smooth(-width,width,src[:,0])
parent=list(range(n))
def find(v):
    while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
    return v
for x,y,z in tri:parent[find(y)]=find(x);parent[find(z)]=find(x)
panels={}
for vi in range(n):panels.setdefault(find(vi),[]).append(vi)
for ids in json.loads((ROOT/'build/skirt_panels.json').read_text()):
    pts=src[ids]
    if pts[:,2].min()<.78 and np.min(pts[:,0])*np.max(pts[:,0])>0:
        r[ids]=1 if pts[:,0].mean()>0 else 0
calf=1-smooth(knee-.13,knee+.17,src[:,2]);hip=smooth(waist-.18,waist+.10,src[:,2]);w=np.zeros((n,28));w[:,0]=hip
w[:,1]=(1-hip)*(1-r)*(1-calf);w[:,2]=(1-hip)*(1-r)*calf;w[:,5]=(1-hip)*r*(1-calf);w[:,6]=(1-hip)*r*calf
edges0=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);eu,ev=edges0.T;uu=np.r_[eu,ev];vv=np.r_[ev,eu];degree0=np.bincount(uu,minlength=n)
bi=np.argsort(-w,axis=1)[:,:4];ww=np.take_along_axis(w,bi,axis=1);ww/=ww.sum(1,keepdims=True)
# Match actual exported byte quantisation before fitting.
bw=np.floor(ww*255).astype(int);bw[:,0]+=255-bw.sum(1);w[:]=0;np.put_along_axis(w,bi,bw/255,axis=1)
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));samples=[]
for label in ['run','bow','riding','idle']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
    frames=list(range(max(1,anim['start']),anim['frames'])) if label!='idle' else [1,507,760,929]
    for f in frames:
        sk=skin_matrices(rig,anim,f);A=np.einsum('nb,bij->nij',w,sk[:,:3,:3]);t=w@sk[:,:3,3];j=pose(rig,anim,f)[:,:3,3]
        # Running is the user's primary failure; include all other motions too.
        samples.append((label,f,A,t,np.linalg.pinv(A),j))
edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);u,v=edges.T;u=np.r_[u,v];v=np.r_[v,u[:len(v)]]
# Keep rear panels on the outer side of the moving calf/knee envelope.
# Sagittal knee flexion collapses rear-facing LBS cloth; lateral clearance
# is stable under that flexion and does not alter front dress decoration.
q=p.copy()
for sign,thigh,calf,foot in [(-1,1,2,3),(1,5,6,7)]:
    take=np.where(p[:,0]*sign>=0)[0];j=rig['restWorld'][:,:3,3]
    anchor=j[thigh];axis=j[foot]-anchor;tt=np.clip((p[take]-anchor)@axis/(axis@axis),0,1);center=anchor+tt[:,None]*axis
    dy=p[take,1]-center[:,1];mask=(1-smooth(.72,.96,src[take,2]))*smooth(0,.07,-dy)
    required=abs(center[:,0])+.085
    q[take,0]+=sign*np.maximum(0,required-abs(q[take,0]))*mask
margin=.008;movable=1-smooth(.94,1.12,src[:,2]);records=[]
def gaps(points,j):
    distances=[];directions=[]
    for start,end,radius in [(1,2,.075),(2,3,.050),(5,6,.075),(6,7,.050)]:
        anchor=j[start];axis=j[end]-anchor;along=np.clip((points-anchor)@axis/(axis@axis),0,1);d=points-anchor-along[:,None]*axis;norm=np.linalg.norm(d,axis=1)
        distances.append(norm-radius);directions.append(d/np.maximum(norm[:,None],1e-8))
    distances=np.array(distances);which=np.argmin(distances,axis=0);ar=np.arange(len(points));return distances[which,ar],np.array(directions)[which,ar]
for iteration in range(100):
    correction=np.zeros_like(q);count=np.zeros(n);worst={}
    for label,f,A,t,inv,j in samples:
        posed=np.einsum('nij,nj->ni',A,q)+t;points=np.r_[posed,posed[tri].mean(1)];gap,direction=gaps(points,j);bad=np.where(gap<margin)[0]
        worst[label]=max(worst.get(label,0),max(0,-float(gap.min())))
        if len(bad)==0:continue
        step=direction[bad]*np.minimum(margin-gap[bad],.012)[:,None]
        vert=bad[bad<n];delta=step[bad<n]
        np.add.at(correction,vert,np.einsum('nij,nj->ni',inv[vert],delta));np.add.at(count,vert,1)
        face=bad[bad>=n]-n;delta=step[bad>=n]
        for col in range(3):
            vi=tri[face,col];np.add.at(correction,vi,np.einsum('nij,nj->ni',inv[vi],delta));np.add.at(count,vi,1)
    correction/=np.maximum(count[:,None],1);q+=correction*.8*movable[:,None]
    # Smooth the displacement only; keep seam/waist and original detail shape.
    delta=q-p;neighbor=np.zeros_like(q);degree=np.zeros(n);np.add.at(neighbor,u,delta[v]);np.add.at(degree,u,1)
    delta=delta*.9+neighbor/np.maximum(degree[:,None],1)*.1
    length=np.linalg.norm(delta,axis=1);limit=.16*movable;delta*=np.minimum(1,limit/np.maximum(length,1e-9))[:,None];q=p+delta
    # Prevent fitting from collapsing triangles or creating needle folds.
    for _ in range(3):
        axis=q[ev]-q[eu];length=np.linalg.norm(axis,axis=1);oldlen=np.linalg.norm(p[ev]-p[eu],axis=1)
        deficit=np.maximum(0,oldlen*.85-length);push=axis/np.maximum(length[:,None],1e-9)*deficit[:,None]*.5
        spring=np.zeros_like(q);np.add.at(spring,eu,-push);np.add.at(spring,ev,push)
        q+=spring/np.maximum(degree0[:,None],1)*movable[:,None]
    if iteration%10==0:print('FIT',iteration,worst,flush=True);records.append({'iteration':iteration,'depth':worst})
np.savez_compressed(ROOT/'build/skirt_clearance_fit.npz',P=q,W=w,source_P=p,object=name)
report={'method':'same-leg calf/thigh anchors plus bounded pose-envelope vertex correction; full run/bow/riding and idle samples; 8mm target capsule clearance','object':name,'width':width,'knee':knee,'waist':waist,'max_rest_displacement_m':float(np.linalg.norm(q-p,axis=1).max()),'iterations':records,'game_solver_used':False}
(ROOT/'reports/skirt_clearance_fit.json').write_text(json.dumps(report,indent=2));print('SKIRT_FIT_READY',report['max_rest_displacement_m'])
