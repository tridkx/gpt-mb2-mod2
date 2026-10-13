"""Fit source-sized collision proxies and compile each final LOD's own cloth."""
import sys,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];WS=workspace_root(R);B=R/'build';C=WS/'tools/cloth_compiler';cfg=json.loads((R/'tools/model_config.json').read_text(encoding='utf8'));prefix=cfg['prefix']
def run(args):subprocess.run([str(x) for x in args],check=True)
transfer=json.loads((R/'reports/weight_transfer.json').read_text());names=transfer['native_bones'];j=np.array(transfer['source_landmarks']);at=lambda n:j[names.index(n)]
source=np.load(B/'fitted_model.npz');manifest=json.loads((B/'manifest.json').read_text());skin=np.concatenate([source[r['object']+'_p'] for r in manifest if 'body' in r['material'].lower()]);caps=[]
def cap(name,a,b,r,ba,bb):
 a=np.array(a);b=np.array(b);assert np.linalg.norm(a-b)>.0001 and 0<r<.3;caps.append(dict(name=name,endpoints_m=[a.tolist(),b.tolist()],radius_m=float(r),bones=[ba,bb]))
def segment_radius(a,b,points,default):
 v=b-a;t=(points-a)@v/(v@v);d=np.linalg.norm(points-a-np.clip(t,0,1)[:,None]*v,axis=1);keep=(t>.12)&(t<.88)&(d<default*2)
 return max(default,float(np.quantile(d[keep],.98))+.004) if keep.sum()>20 else default
# Radii scale with this source's measured skeletal dimensions, then fit visible
# skin samples. Covered torso areas remain proxies and require game inspection.
hipwidth=np.linalg.norm(at('l_thigh')-at('r_thigh'));bodyheight=float(transfer['height_m']);pelvis=at('pelvis');spine=at('spine');neck=at('neck');head=at('head')
for pre in ['l','r']:
 for label,a,b,ba,bb,ratio in [('thigh',at(pre+'_thigh'),at(pre+'_calf'),pre+'_thigh',pre+'_calf',.15),('calf',at(pre+'_calf'),at(pre+'_foot'),pre+'_calf',pre+'_foot',.105),('upperarm',at(pre+'_upperarm_twist'),at(pre+'_foretwist'),pre+'_upperarm_twist',pre+'_foretwist',.105),('forearm',at(pre+'_foretwist'),at(pre+'_hand'),pre+'_foretwist',pre+'_hand',.10)]:
  default=np.linalg.norm(b-a)*ratio;r=segment_radius(a,b,skin,default);cap(pre+'_'+label,a+(b-a)*.08,b-(b-a)*.08,r,ba,bb)
cap('waist',spine,at('spine1'),hipwidth*.42,'spine','spine1')
for offset in [-.28,0,.28]:
 a=pelvis.copy();a[0]+=hipwidth*offset;a[2]-=hipwidth*.20;b=a.copy();b[2]+=hipwidth*.62;cap('pelvis_'+str(offset),a,b,hipwidth*.43,'pelvis','pelvis')
cap('back',at('spine1'),at('spine2'),hipwidth*.38,'spine1','spine2')
cap('neck',neck,head,bodyheight*.016,'neck','head')
a=head.copy();b=head.copy();b[2]+=bodyheight*.065;cap('head',a,b,bodyheight*.037,'head','head')
if cfg.get('collision_refit'):
 from refit_skirt_collision import fit,fit_pose_envelope,fit_waist_roots
 fitting=fit(caps,source,manifest,transfer,cfg,R)
 fitting['waist_roots']=fit_waist_roots(caps,source,manifest,transfer,cfg,R)
 fitting['pose_envelope']=fit_pose_envelope(caps,source,manifest,transfer,cfg,R)
 (R/'reports/collision_refit.json').write_text(json.dumps(fitting,indent=2))
root=ET.Element('bodies');body=ET.SubElement(root,'body',name=prefix+'_collision',owner_skeleton=cfg['skeleton']);container=ET.SubElement(body,'capsules')
for row in caps:
 a,b=np.array(row['endpoints_m']);u=b-a;length=np.linalg.norm(u);u/=length;v=np.cross(u,[1,0,0] if abs(u[1])>.9 else [0,1,0]);v/=np.linalg.norm(v);t=np.cross(v,u);frame=np.eye(4);frame[:3,:3]=[u,t,v];frame[3,:3]=a
 node=ET.SubElement(container,'capsule',name=prefix+'_'+row['name'],length=f'{length:.6f}',origin='0, 0, 0',frame=', '.join(f'{x:.6f}' for x in frame.ravel()));points=ET.SubElement(node,'points')
 for i,bone in enumerate(row['bones']):
  point=ET.SubElement(points,'point',radius=f"{row['radius_m']:.6f}");bones=ET.SubElement(point,'bones')
  influences=row.get('endpoint_weights',[[dict(bone=b,weight=1.)] for b in row['bones']])[i]
  assert 1<=len(influences)<=2 and abs(sum(v['weight'] for v in influences)-1)<1e-6
  for influence in influences:ET.SubElement(bones,'bone',name=influence['bone'],weight=f"{influence['weight']:.9f}")
ET.indent(root,space='  ');ET.ElementTree(root).write(R/'module'/cfg['id']/'ModuleData/cloth_bodies.xml',encoding='utf8',xml_declaration=True)
(R/'reports/cloth_collision.json').write_text(json.dumps(dict(capsules=caps,engine_verified=False,scope='Same-side anatomical thigh surfaces; model-specific shorts guard where configured; remaining covered torso uses retained dimension-scaled proxies'),indent=2))
if cfg.get('collision_refit',{}).get('shorts_guard'):
 run([sys.executable,R/'tools/verify_skirt_surface.py','--fit'])
if '--collision-only' in sys.argv:sys.exit(0)
for project,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch')]:run(['dotnet','build',C/(project+'.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(B/'cloth_obj'/project)+'/','-o',B/folder])
(B/'cloth_inputs').mkdir(exist_ok=True)
probe=subprocess.run(['dotnet',str(B/'cloth_probe/NativeClothProbe.dll'),str(B/'uncooked.tpac'),prefix+'_body','--dump-segments',str(B/'cloth_inputs')],check=True,capture_output=True,text=True)
(R/'reports/cloth_uncooked.json').write_text(probe.stdout)
meshes=[json.loads(p.read_text()) for p in (B/'cloth_inputs').glob('*.mesh.json')];assert meshes and {m['lod'] for m in meshes}==set(cfg['cloth_lods'])
# Each permitted source part has an explicit upper-edge attachment policy.
# Roots lost to decimation/package splitting are recorded by the compiler.
active={r['object']:r for r in json.loads((R/'reports/cloth_paint.json').read_text())['rows'] if r['active_vertices']}
policy={'default':{'unanchored':'error'},'meshes':{}}
for mesh in meshes:
 if any(mesh['name'].startswith(n) for n in active):policy['meshes'][mesh['name']]={'unanchored':'pin_upper','axis':2,'band_m':.008,'min_vertices':2,'reason':'Restore surviving upper attachment edge of explicitly painted hanging component after reduction/splitting'}
(R/'tools/cloth_policy.json').write_text(json.dumps(policy,indent=2))
run([sys.executable,R/'tools/cook_meshes.py'])
run(['dotnet',B/'cloth_patch/ClothPatch.dll',B/'uncooked.tpac',B/'cooked_cloth/manifest.json',R/'module'/cfg['id']/'AssetPackages'/(prefix+'.tpac'),'--allow-metameshes',prefix+'_body'])
print('CLOTH_COOKED',cfg['id'],len(meshes))
