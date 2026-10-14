"""Fit capsule dimensions from each selected model's measured bind geometry."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
import numpy as np
from context import config
def write_collisions(root):
    c=config(root);t=json.loads((root/'reports/weight_transfer.json').read_text(encoding='utf8'));S=np.array(t['source_landmarks']);a=np.load(root/'build/fitted_model.npz');manifest=json.loads((root/'build/manifest.json').read_text(encoding='utf8'));parts=[a[r['object']+'_p'] for r in manifest if r['kind']!='hair'];p=np.concatenate(parts);shoulder=float(np.linalg.norm(S[15]-S[22]));caps=[];measure=[]
    for name,i,j in [('torso_low',9,10),('torso_high',10,11)]:
        band=p[(p[:,2]>=S[i,2]-.02)&(p[:,2]<=S[j,2]+.035)&(abs(p[:,0])<shoulder*.32)]
        if len(band)<12:band=p[(abs(p[:,2]-S[j,2])<.055)&(abs(p[:,0])<shoulder*.35)]
        assert len(band)>5,(c['id'],name)
        lo,hi=np.quantile(band[:,1],[.08,.92]);center=(lo+hi)/2;radius=float(np.clip((hi-lo)*.4,.035,.085));aa=S[i].copy();bb=S[j].copy();aa[1]=bb[1]=center;caps.append((name,aa,bb,radius,t['native_bones'][i],t['native_bones'][j]));measure.append({'name':name,'samples':len(band),'front_back_bounds_m':[float(lo),float(hi)],'center_y_m':float(center)})
    face=[]
    for rec in manifest:
        if rec['source_material_index'] in c.get('glass_materials',[]):continue
        if any(x in rec['source_material'] for x in ['面','颜','脸','眼白','白目']):face.append(a[rec['object']+'_p'])
    if not face:face=[p[p[:,2]>S[13,2]]]
    fp=np.concatenate(face);width=float(np.ptp(fp[:,0]));radius=float(np.clip(width*.42,.045,.09));zlo,zhi=np.quantile(fp[:,2],[.15,.8]);aa=S[13].copy();bb=S[13].copy();aa[2]=max(float(zlo),S[13,2]+.015);bb[2]=max(float(zhi),aa[2]+.035);caps.append(('head',aa,bb,radius,'head','head'));neck_radius=radius*.38;caps.append(('neck',S[12],S[13],neck_radius,'neck','head'))
    for side,i,j in [('l',15,17),('r',22,24)]:caps.append((side+'_upperarm',S[i],S[j],float(np.linalg.norm(S[j]-S[i])*.105),t['native_bones'][i],t['native_bones'][j]))
    xml=ET.Element('bodies');body=ET.SubElement(xml,'body',name=c['prefix']+'_collision',owner_skeleton=c['skeleton']);container=ET.SubElement(body,'capsules');rows=[]
    for name,aa,bb,r,ba,bbone in caps:
        axis=bb-aa;length=np.linalg.norm(axis);u=axis/length;v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);third=np.cross(v,u);frame=np.eye(4);frame[:3,:3]=[u,third,v];frame[3,:3]=aa;node=ET.SubElement(container,'capsule',name=c['prefix']+'_'+name,length=f'{length:.6f}',origin='0, 0, 0',frame=', '.join(f'{x:.6f}' for x in frame.ravel()));points=ET.SubElement(node,'points')
        for bone in [ba,bbone]:point=ET.SubElement(points,'point',radius=f'{r:.6f}');bones=ET.SubElement(point,'bones');ET.SubElement(bones,'bone',name=bone,weight='1.0')
        rows.append({'name':name,'endpoints_m':[aa.tolist(),bb.tolist()],'radius_m':r,'bones':[ba,bbone]})
    ET.indent(xml,space='  ');ET.ElementTree(xml).write(root/'module'/c['id']/'ModuleData/cloth_bodies.xml',encoding='utf8',xml_declaration=True);(root/'reports/cloth_collision.json').write_text(json.dumps({'model':c['id'],'method':'Model-specific measured central torso depth, source face width and limb length','measurements':measure,'capsules':rows,'game_verified':False},indent=2))
