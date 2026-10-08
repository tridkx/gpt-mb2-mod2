"""Evaluate reference-style calf follow without moving the accepted contour."""
import sys,json
from pathlib import Path
import numpy as np
WS=Path(__file__).resolve().parents[1];ROOT=WS/'mods'/sys.argv[1];BASE=ROOT/'build/repair_baseline_v1.0.0'
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,pose,lbs
# Reuse this model's measured landmarks and its distance-weighting function.
script=ROOT/'tools/rig_model.py';text=script.read_text();head=text.split('bpy.ops.wm.read_factory_settings')[0].replace('import bpy, json, sys, re','import json, sys, re').replace('from mathutils import Matrix, Vector','')
env={'__file__':str(script)};exec(compile(head,str(script),'exec'),env)
smooth=env['smooth'];weights=env['weights'];normalize=env['normalize']
arrays=np.load(BASE/'rig_arrays.npz');manifest=json.loads((BASE/'rig_manifest.json').read_text());name=next(m['object'] for m in manifest if m['kind']=='skirt');p=arrays[name+'_P'];src=arrays[name+'_S'];tri=np.array(json.loads((ROOT/'build/skirt_triangles.json').read_text()));edges=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);u,v=edges.T;length=np.linalg.norm(p[u]-p[v],axis=1);valid=length>.003
rig=parse_skeljson(json.loads((ROOT/'reports/human_skeleton.json').read_text()));samples=[]
for label in ['run','bow','riding','idle']:
    anim=parse_animjson(json.loads((ROOT/'reports'/(label+'.json')).read_text()));frames=range(max(1,anim['start']),anim['frames']) if label!='idle' else sorted(set(np.linspace(1,anim['frames']-1,16).astype(int)))
    for frame in frames:samples.append((label,frame,skin_matrices(rig,anim,frame),pose(rig,anim,frame)[:,:3,3]))
def quantize(w):
    bi=np.argsort(-w,axis=1)[:,:4];bw=np.take_along_axis(w,bi,axis=1);bw/=bw.sum(1,keepdims=True);q=np.floor(bw*255).astype(int);q[:,0]+=255-q.sum(1);full=np.zeros_like(w);np.put_along_axis(full,bi,q/255,axis=1);return full,bi,q
def evaluate(w):
    full,bi,bw=quantize(w);result={}
    for label,frame,sk,j in samples:
        posed=lbs(p,bi,bw,sk);points=np.r_[posed,posed[tri].mean(1)];gaps=[]
        for a,b,r in [(1,2,.075),(2,3,.050),(5,6,.075),(6,7,.050)]:
            axis=j[b]-j[a];t=np.clip((points-j[a])@axis/(axis@axis),0,1);gaps.append(np.linalg.norm(points-j[a]-t[:,None]*axis,axis=1)-r)
        depth=np.maximum(0,-np.min(gaps,axis=0));ratio=np.linalg.norm(posed[u[valid]]-posed[v[valid]],axis=1)/length[valid];entry=result.setdefault(label,{'depth':0,'contacts':0,'stretch':0,'p99':0,'severity':0})
        entry['depth']=max(entry['depth'],float(depth.max()));entry['contacts']=max(entry['contacts'],int((depth>0).sum()));entry['severity']+=float((depth**2).sum());entry['stretch']=max(entry['stretch'],float(ratio.max()));entry['p99']=max(entry['p99'],float(np.quantile(ratio,.99)))
    return full,result
baseline=evaluate(arrays[name+'_W'])[1];results=[];folder=ROOT/'build/reference_skirt_candidates';folder.mkdir(exist_ok=True)
settings=json.loads((ROOT/'tools/model_config.json').read_text()).get('skirt_reference_calibration',{})
for anchor in settings.get('waist_modes',['reference','pelvis']):
    waist=weights(src,[0,9,10]) if anchor=='reference' else np.eye(28)[np.zeros(len(src),int)]
    for follow in settings.get('follow_candidates',[.7,.8,.9]):
        for amount,width in [(a,b) for a in settings.get('calf_candidates',[.15,.25,.35,.45]) for b in settings.get('width_candidates',[.12])]:
            right=smooth(-width,width,src[:,0]);low=1-smooth(.4,.78,src[:,2]);legs=np.zeros_like(waist)
            left_calf=low*amount*(1-smooth(-width,0,src[:,0]));right_calf=low*amount*smooth(0,width,src[:,0])
            legs[:,1]=(1-right)*(1-left_calf);legs[:,2]=(1-right)*left_calf;legs[:,5]=right*(1-right_calf);legs[:,6]=right*right_calf
            f=follow*(1-smooth(.87,1.09,src[:,2]));w=waist*(1-f[:,None])+legs*f[:,None];w,result=evaluate(w);key=f'{anchor}_{follow}_{amount}'+(f'_width{width}' if width!=.12 else '');np.savez_compressed(folder/(key+'.npz'),P=p,W=w,A=arrays[name+'_A'],object=name)
            score=sum(result[k]['severity']/max(baseline[k]['severity'],1e-8) for k in ['run','bow','riding'])
            entry={'key':key,'waist':anchor,'follow':follow,'calf':amount,'width':width,'score':score,'stats':result,'safe_deformation':all(s['stretch']<4 and s['p99']<3 for s in result.values())};results.append(entry)
results.sort(key=lambda x:(not x['safe_deformation'],x['score']));report={'reference':'user-accepted TianxiangRenqiu calf-follow recipe; model-specific measured landmarks, immutable rest contour','baseline':baseline,'candidates':results,'rest_contour_changed':False,'game_verified':False};(ROOT/'reports/reference_skirt_calibration.json').write_text(json.dumps(report,indent=2));print('BASELINE',baseline);print('BEST',json.dumps(results[:4]))
