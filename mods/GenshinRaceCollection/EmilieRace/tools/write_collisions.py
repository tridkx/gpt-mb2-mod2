"""Bind-space capsules sized for this character's head, torso and shoulders."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
import numpy as np
R=Path(__file__).resolve().parents[1];t=json.loads((R/'reports/weight_transfer.json').read_text(encoding='utf8'));S=np.array(t['source_landmarks']);caps=[]
for name,i,j,r in [('torso_low',9,10,.06),('torso_high',10,11,.07),('neck',12,13,.035),('l_upperarm',15,17,.025),('r_upperarm',22,24,.025)]:caps.append((name,S[i],S[j],r,t['native_bones'][i],t['native_bones'][j]))
caps.append(('head',S[13]+[0,0,.03],S[13]+[0,0,.115],.076,'head','head'))
root=ET.Element('bodies');body=ET.SubElement(root,'body',name='emilie_collision',owner_skeleton='emilie_skeleton');container=ET.SubElement(body,'capsules');report=[]
for name,a,b,r,ba,bb in caps:
 axis=b-a;length=np.linalg.norm(axis);u=axis/length;v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);tangent=np.cross(v,u);frame=np.eye(4);frame[:3,:3]=[u,tangent,v];frame[3,:3]=a
 node=ET.SubElement(container,'capsule',name='emilie_'+name,length=f'{length:.6f}',origin='0, 0, 0',frame=', '.join(f'{x:.6f}' for x in frame.ravel()));points=ET.SubElement(node,'points')
 for bone in [ba,bb]:point=ET.SubElement(points,'point',radius=f'{r:.6f}');bones=ET.SubElement(point,'bones');ET.SubElement(bones,'bone',name=bone,weight='1.0')
 report.append({'name':name,'endpoints_m':[a.tolist(),b.tolist()],'radius_m':r,'bones':[ba,bb]})
ET.indent(root,space='  ');ET.ElementTree(root).write(R/'module/EmilieRace/ModuleData/cloth_bodies.xml',encoding='utf8',xml_declaration=True);(R/'reports/cloth_collision.json').write_text(json.dumps({'capsules':report,'game_verified':False},indent=2))
