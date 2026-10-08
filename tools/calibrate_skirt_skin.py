"""Calibrate height-based same-leg skirt skinning on preserved final geometry.
Runs without cloth physics; rejects motion penetration rather than just tears.
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
from baker.animation import parse_animjson,skin_matrices,pose,lbs
cfg=json.loads((ROOT/'tools/model_config.json').read_text(encoding='utf-8'));a=np.load(BASE/'rig_arrays.npz');fit=json.loads((BASE/'reports/rig_fit.json').read_text());skirt=next(r['object'] for r in fit['parts'] if r['kind']=='skirt')
meshes=[m for f in (BASE/'export/geo').glob('*.bin') for m in read_geo(f)];m=next(m for m in meshes if m['name']==skirt)
p=m['pos'];_,vi=cKDTree(a[skirt+'_P']).query(p);src=a[skirt+'_S'][vi];tri=m['idx'].reshape(-1,3);edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);ia,ib=edges.T
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));samples=[]
for label in ['run','bow','riding','idle']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()))
    frames=range(max(1,anim['start']),anim['frames']) if label!='idle' else [1,507,760,929]
    for f in frames:samples.append((label,f,pose(rig,anim,f)[:,:3,3],skin_matrices(rig,anim,f)))
def smooth(lo,hi,x):t=np.clip((x-lo)/(hi-lo),0,1);return t*t*(3-2*t)
def weights(q,width,knee,waist):
    r=smooth(-width,width,q[:,0]);c=1-smooth(knee-.13,knee+.17,q[:,2]);w0=smooth(waist-.18,waist+.10,q[:,2]);w=np.zeros((len(q),28))
    w[:,0]=w0;w[:,1]=(1-w0)*(1-r)*(1-c);w[:,2]=(1-w0)*(1-r)*c;w[:,5]=(1-w0)*r*(1-c);w[:,6]=(1-w0)*r*c
    ids=np.argsort(-w,axis=1)[:,:4];bw=np.take_along_axis(w,ids,axis=1);bw/=bw.sum(1,keepdims=True)
    return ids,bw*255
def evaluate(q,bi,bw):
    rest=np.linalg.norm(q[ia]-q[ib],axis=1);valid=rest>.003;out={}
    for label,f,joints,skin in samples:
        posed=lbs(q,bi,bw,skin);points=np.concatenate([posed,posed[tri].mean(1)]);gap=[]
        for j,k,r in [(1,2,.075),(2,3,.050),(5,6,.075),(6,7,.050)]:
            anchor=joints[j];axis=joints[k]-anchor;t=np.clip((points-anchor)@axis/(axis@axis),0,1);gap.append(np.linalg.norm(points-anchor-t[:,None]*axis,axis=1)-r)
        g=np.min(gap,axis=0);entry=out.setdefault(label,{'depth':0,'samples':0,'stretch':0})
        entry['depth']=max(entry['depth'],max(0,-float(g.min())));entry['samples']=max(entry['samples'],int((g<0).sum()))
        entry['stretch']=max(entry['stretch'],float((np.linalg.norm(posed[ia[valid]]-posed[ib[valid]],axis=1)/rest[valid]).max()))
    return out
results=[]
for width in [.065,.10,.14]:
    for knee in [.58,.65,.72]:
        ids,bw=weights(src,width,knee,.98)
        stats=evaluate(p,ids,bw);results.append({'width':width,'knee':knee,'waist':.98,'stats':stats})
results.sort(key=lambda r:(r['stats']['run']['samples'],r['stats']['run']['depth']))
base=evaluate(p,m['bi'],m['bw']);(ROOT/'reports/skirt_skin_calibration.json').write_text(json.dumps({'baseline':base,'candidates':results},indent=2))
print('BASELINE',json.dumps(base));print('BEST',json.dumps(results[:3]))
