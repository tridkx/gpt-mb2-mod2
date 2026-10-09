"""Fit a Mingyu-only posterior torso collider; preserve validated leg body."""
import json,sys,hashlib,argparse,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--back-inset',type=float,default=.008)
parser.add_argument('--top-height',type=float,default=1.30)
parser.add_argument('--report',default='reports/back_collision_fit.json')
args=parser.parse_args()
WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'));sys.path.insert(0,str(WS/'tools/asset_helpers/previewer'))
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,skin_matrices,lbs
meshes=[m for f in (ROOT/'build/final_export/geo').glob('*.bin') for m in read_geo(f)]
hair=next(m for m in meshes if m['name']=='sx_mingyu_head_00')
torso=np.concatenate([m['pos'] for m in meshes if m['name'] in ['sx_mingyu_body_01','sx_mingyu_body_02']])
torso=torso[(abs(torso[:,0])<.13)&(torso[:,1]<.015)]
rawskel=json.loads((ROOT/'reports/human_skeleton.json').read_text());rig=parse_skeljson(rawskel)
lookup={b['name']:b['i'] for b in rawskel['bones']}
xml=ROOT/'module/ShengxiuCollection/ModuleData/cloth_bodies.xml'
tree=ET.parse(xml);root=tree.getroot();leg=next(b for b in root if b.get('name')=='sx_mingyu_leg_collision')
leg_bytes=ET.tostring(leg)
for b in list(root):
 if b.get('name')=='sx_mingyu_back_collision':root.remove(b)
body=ET.SubElement(root,'body',{'name':'sx_mingyu_back_collision','owner_skeleton':'human_skeleton'})
caps=ET.SubElement(body,'capsules');rows=[]
surface=[]
for height in [.96,args.top_height]:
 band=torso[abs(torso[:,2]-height)<.055];assert len(band)>5
 surface.append(float(np.quantile(band[:,1],.04)))
for column in [-.065,0,.065]:
 radius=.045
 ends=np.array([[column,surface[0]+radius+args.back_inset,.96],[column,surface[1]+radius+args.back_inset,args.top_height]])
 axis=ends[1]-ends[0];length=np.linalg.norm(axis);x=axis/length
 z=np.cross(x,[0,1,0]);z/=np.linalg.norm(z);y=np.cross(z,x)
 frame=np.eye(4);frame[:3,:3]=[x,y,z];frame[3,:3]=ends[0]
 cap=ET.SubElement(caps,'capsule',{'name':f'sx_mingyu_back_{column:.3f}','length':f'{length:.6f}','origin':'0.000, 0.000, 0.000','frame':', '.join(f'{v:.6f}' for v in frame.ravel())})
 points=ET.SubElement(cap,'points')
 for i in range(2):
  point=ET.SubElement(points,'point',{'radius':f'{radius:.6f}'});bones=ET.SubElement(point,'bones')
  ET.SubElement(bones,'bone',{'name':'spine' if i==0 else 'spine2','weight':'1.000'})
 rows.append({'name':cap.get('name'),'back_surface_y_m':surface,'radius_m':radius,'endpoints_m':ends.tolist(),'endpoint_bones':['spine','spine2']})
assert ET.tostring(leg)==leg_bytes
ET.indent(tree,space='  ');tree.write(xml,encoding='utf-8',xml_declaration=True);xml.write_bytes(xml.read_bytes().replace(b'\r\n',b'\n'))
def endpoints(cap):
 f=np.fromstring(cap.get('frame'),sep=',').reshape(4,4)
 return np.array([f[3,:3],f[3,:3]+f[0,:3]*float(cap.get('length'))])
def project(p,cap,skin):
 ends=endpoints(cap);points=cap.findall('./points/point')
 for i,point in enumerate(points):
  b=lookup[point.find('./bones/bone').get('name')];ends[i]=skin[b,:3,:3]@ends[i]+skin[b,:3,3]
 axis=ends[1]-ends[0];size=np.linalg.norm(axis);direction=axis/(size+.00001)
 t=np.clip((p-ends[0])@direction,0,size);center=ends[0]+t[:,None]*direction
 r=float(points[0].get('radius'));delta=p-center;length=np.linalg.norm(delta,axis=1)
 return center+delta*(np.maximum(length,r)/np.maximum(length,1e-12))[:,None]
diagnostics=[]
for label in ['idle','run']:
 anim=parse_animjson(json.loads((ROOT/f'reports/{label}.json').read_text()))
 frames=[max(1,anim['start'])] if label=='idle' else range(max(1,anim['start']),anim['frames'])
 for frame in frames:
  skin=skin_matrices(rig,anim,frame);p=lbs(hair['pos'],hair['bi'],hair['bw'],skin);moved=p.copy()
  for cap in caps:moved=project(moved,cap,skin)
  offset=moved-p
  diagnostics.append({'animation':label,'frame':int(frame),'projected_vertices':int((np.linalg.norm(offset,axis=1)>.0001).sum()),'max_lift_m':float(offset[:,2].max()),'max_projection_m':float(np.linalg.norm(offset,axis=1).max()),'worst_lift_rest_position':hair['pos'][np.argmax(offset[:,2])].tolist()})
report={'status':'pass','body_name':body.get('name'),'back_surface_inset_m':args.back_inset,'top_height_m':args.top_height,'xml_sha256':hashlib.sha256(xml.read_bytes()).hexdigest(),'leg_body_unchanged':True,'capsules':rows,'hair_projection_diagnostics':diagnostics,'scope':'Own back surface fitting and native skeletal motion, no engine cloth/dummy collision. Only posterior torso, no scalp or chest capsule; all hair geometry and solver distances unchanged.'}
(ROOT/args.report).write_text(json.dumps(report,indent=2),encoding='utf-8')
print('BACK_BODY_FITTED',diagnostics[0],'; run max lift',max(d['max_lift_m'] for d in diagnostics),flush=True)
