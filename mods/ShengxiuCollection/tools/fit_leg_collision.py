"""Mingyu-only leg collision fitting and offline capsule diagnostics."""
import json,sys,copy,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'))
sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
NATIVE=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/ModuleData/cloth_bodies.xml')
rawskel=json.loads((ROOT/'reports/human_skeleton.json').read_text());rig=parse_skeljson(rawskel)
lookup={b['name']:b['i'] for b in rawskel['bones']}
meshes=[m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f)]
leg=next(m for m in meshes if m['name']=='sx_mingyu_legs_04')
skirt=next(m for m in meshes if m['name']=='sx_mingyu_body_06')
native=next(b for b in ET.parse(NATIVE).getroot() if b.get('name')=='human_body')
custom=ET.Element('body',{'name':'sx_mingyu_leg_collision','owner_skeleton':'human_skeleton'})
caps=ET.SubElement(custom,'capsules');rows=[]
def endpoints(cap):
 f=np.fromstring(cap.get('frame'),sep=',').reshape(4,4);o=np.fromstring(cap.get('origin'),sep=',')
 return np.array([o@f[:3,:3]+f[3,:3],(o+np.array([float(cap.get('length')),0,0]))@f[:3,:3]+f[3,:3]])
def gap(p,ends,radii):
 axis=ends[1]-ends[0];length=np.linalg.norm(axis);direction=axis/(length+.00001)
 t=np.clip((p-ends[0])@direction,0,length)
 center=ends[0]+t[:,None]*direction;r=radii[0]+(radii[1]-radii[0])*t/(length+.00001)
 delta=p-center;dist=np.linalg.norm(delta,axis=1)
 return dist-r,delta*(np.maximum(dist,r)/np.maximum(dist,1e-12)-1)[:,None],t/length
for name in ['l_thigh','r_thigh','l_calf','r_calf']:
 cap=copy.deepcopy(next(c for c in native.findall('./capsules/capsule') if c.get('name')==name))
 bone=lookup[name];dominant=(leg['bi']==bone)*leg['bw']/255
 ids=dominant.sum(1)>.5
 q=leg['pos'][ids]
 # Fit the centre line too: Mingyu's lower legs are displaced backwards and
 # sideways relative to the native proxy. Inflating its radius would push skirts.
 bins=np.linspace(np.quantile(q[:,2],.08),np.quantile(q[:,2],.92),7)
 centers=[]
 for lo,hi in zip(bins[:-1],bins[1:]):
  band=q[(q[:,2]>=lo)&(q[:,2]<=hi)]
  if len(band)<3:continue
  centers.append(np.r_[(band[:,:2].min(0)+band[:,:2].max(0))*.5,np.median(band[:,2])])
 centers=np.asarray(centers);coef=np.polyfit(centers[:,2],centers[:,:2],1)
 ztop,zbottom=(.82,.51) if 'thigh' in name else (.48,.14)
 ends=np.array([np.r_[ztop*coef[0]+coef[1],ztop],np.r_[zbottom*coef[0]+coef[1],zbottom]])
 radial,_,t=gap(q,ends,[0,0]);inner=(t>.05)&(t<.95)
 radius=float(np.quantile(radial[inner],.98)+.003)
 assert .02<radius<.09,(name,radius)
 axis=ends[1]-ends[0];length=np.linalg.norm(axis);x=axis/length
 z=np.cross(x,[0,1,0]);z/=np.linalg.norm(z);y=np.cross(z,x)
 fitted_frame=np.eye(4);fitted_frame[:3,:3]=[x,y,z];fitted_frame[3,:3]=ends[0]
 cap.set('frame',', '.join(f'{v:.6f}' for v in fitted_frame.ravel()))
 cap.set('length',f'{length:.6f}')
 original=[float(p.get('radius')) for p in cap.findall('./points/point')]
 for p in cap.findall('./points/point'):p.set('radius',f'{radius:.6f}')
 caps.append(cap);row={'name':name,'bone':bone,'sample_vertices':int(inner.sum()),'original_radii_m':original,'fitted_radius_m':radius,'skin_radial_p98_m':radius-.003,'fitted_endpoints_m':ends.tolist()}
 rows.append(row);print(row,flush=True)
tree=ET.ElementTree(ET.Element('bodies'));tree.getroot().append(custom);ET.indent(tree,space='  ')
dest=ROOT/'module/ShengxiuCollection/ModuleData/cloth_bodies.xml'
tree.write(dest,encoding='utf-8',xml_declaration=True);dest.write_bytes(dest.read_bytes().replace(b'\r\n',b'\n'))
diagnostics=[]
for label in ['idle','run']:
 anim=parse_animjson(json.loads((ROOT/f'reports/{label}.json').read_text()))
 frames=range(max(1,anim['start']),anim['frames']) if label=='run' else [max(1,anim['start'])]
 for frame in frames:
  skin=skin_matrices(rig,anim,frame);p=lbs(skirt['pos'],skirt['bi'],skirt['bw'],skin);moved=p.copy()
  max_skin_gap=0
  for cap in caps:
   ends=endpoints(cap);points=cap.findall('./points/point')
   for i,point in enumerate(points):
    bindings=[(lookup[b.get('name')],float(b.get('weight'))) for b in point.findall('./bones/bone')]
    ends[i]=sum((skin[b,:3,:3]@ends[i]+skin[b,:3,3])*w for b,w in bindings)
   radii=[float(pt.get('radius')) for pt in points]
   g,delta,_=gap(moved,ends,radii);moved+=delta
  delta=moved-p
  diagnostics.append({'animation':label,'frame':int(frame),'inside_vertices':int((np.linalg.norm(delta,axis=1)>.0001).sum()),'max_lift_m':float(delta[:,2].max()),'max_projection_m':float(np.linalg.norm(delta,axis=1).max())})
report={'status':'pass','body_name':custom.get('name'),'native_cloth_bodies_sha256':hashlib.sha256(NATIVE.read_bytes()).hexdigest(),'custom_xml_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'capsules':rows,'skirt_projection_diagnostics':diagnostics,'head_collision_remains_disabled':True,'scope':'Own leg skin radius fitting and native skeletal poses. Capsule interpretation assumes frame X length. Does not run game cloth or dummy collision; custom XML engine loading requires game confirmation.'}
(ROOT/'reports/leg_collision_fit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('LEG_BODY_FITTED',len(diagnostics),'frames; max lift',max(d['max_lift_m'] for d in diagnostics),flush=True)
