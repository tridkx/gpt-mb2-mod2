"""Posterior garment-sized capsules for freely moving Mingyu long hair."""
import json,hashlib,shutil,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hair_shape_analysis import read_geo
path=ROOT/'module/ShengxiuCollection/ModuleData/cloth_bodies.xml'
backup=ROOT/'build/back_hair_baseline_v1.1.6/cloth_bodies.xml'
if not backup.exists():shutil.copy2(path,backup)
tree=ET.parse(backup);root=tree.getroot()
leg=ET.tostring(next(b for b in root if b.get('name')=='sx_mingyu_leg_collision'))
body=next(b for b in root if b.get('name')=='sx_mingyu_back_collision');body.clear()
body.attrib.update(name='sx_mingyu_back_collision',owner_skeleton='human_skeleton')
caps=ET.SubElement(body,'capsules')
profile=json.loads((ROOT/'reports/back_hair_source_fit.json').read_text())
z=np.array(profile['profile_z_m']);surface=np.array(profile['body_back_y_m'])
points=[];weights=[]
for f in (ROOT/'build/head_neck_final_export/geo').glob('*.bin'):
 for m in read_geo(f):
  if m['name'] not in ['sx_mingyu_body_01','sx_mingyu_body_02']:continue
  w=np.zeros((len(m['pos']),28));np.add.at(w,(np.arange(len(w))[:,None],m['bi']),m['bw']/255)
  keep=(abs(m['pos'][:,0])<.09)&(m['pos'][:,1]<-.015)
  points.append(m['pos'][keep]);weights.append(w[keep])
p=np.concatenate(points);w=np.concatenate(weights)
bone_names={b['i']:b['name'] for b in json.loads((ROOT/'reports/human_skeleton.json').read_text())['bones']}
heights=[.84,1.16,1.30,1.39,1.44];radii=[.07,.07,.065,.04,.025];margin=.012;rows=[]
for x in [-.12,-.08,-.04,0,.04,.08,.12]:
 for segment,(a,b) in enumerate(zip(heights[:-1],heights[1:])):
  ends=np.array([[x,np.interp(h,z,surface)+radii[segment+i]-margin,h] for i,h in enumerate([a,b])])
  axis=ends[1]-ends[0];length=np.linalg.norm(axis);u=axis/length
  v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);t=np.cross(v,u)
  frame=np.eye(4);frame[:3,:3]=[u,t,v];frame[3,:3]=ends[0]
  cap=ET.SubElement(caps,'capsule',name=f'sx_mingyu_free_back_{x:.3f}_{segment}',length=f'{length:.6f}',origin='0.000, 0.000, 0.000',frame=', '.join(f'{value:.6f}' for value in frame.ravel()))
  cps=ET.SubElement(cap,'points');bindings=[]
  for endpoint,height in enumerate([a,b]):
   ids=np.argsort(abs(p[:,2]-height))[:12];weight=w[ids].mean(0)
   bones=np.argsort(-weight)[:2];weight=weight[bones];weight/=weight.sum()
   point=ET.SubElement(cps,'point',radius=f'{radii[segment+endpoint]:.6f}');groups=ET.SubElement(point,'bones')
   bind=[]
   for bone,value in zip(bones,weight):
    if value<1e-6:continue
    ET.SubElement(groups,'bone',name=bone_names[int(bone)],weight=f'{value:.6f}')
    bind.append([bone_names[int(bone)],float(value)])
   bindings.append(bind)
  rows.append(dict(name=cap.get('name'),endpoints_m=ends.tolist(),radii_m=radii[segment:segment+2],bindings=bindings))
assert ET.tostring(next(b for b in root if b.get('name')=='sx_mingyu_leg_collision'))==leg
ET.indent(tree,space='  ');tree.write(path,encoding='utf-8',xml_declaration=True)
path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n'))
report=dict(status='pass',capsules=rows,posterior_surface_margin_m=margin,top_center_height_m=1.44,leg_collision_body_unchanged=True,xml_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),scope='Rest garment profile; actual capsule projection and CPU cloth diagnostic checked separately; game solver not run.')
(ROOT/'reports/free_hair_collision_fit.json').write_text(json.dumps(report,indent=2))
print('FREE_HAIR_COLLISION_FITTED',len(rows),'capsules; leg collision unchanged')
