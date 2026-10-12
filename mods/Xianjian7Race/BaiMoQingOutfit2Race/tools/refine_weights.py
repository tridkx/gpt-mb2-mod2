"""Model-scaled shoulder blending and attachment weights for hanging panels."""
import numpy as np
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def refine(me,ob,p,w,cfg,source,ni):
 # Collapse hanging helper chains to their actual upper attachment, rather
 # than letting a continuous skirt interpolate across independently moving legs.
 reports=[];hanging=set()
 for mi,slot in enumerate(ob.material_slots):
  material=slot.material.name;rules=[r for r in cfg['cloth_rules'] if r['material']==material]
  if not rules:continue
  faces=[f for f in me.polygons if f.material_index==mi];ids=sorted({int(v) for f in faces for v in f.vertices});q,owner=np.unique(np.round(p[ids],6),axis=0,return_inverse=True);where={v:i for i,v in enumerate(ids)};parents=list(range(len(q)))
  def root(i):
   while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
   return i
  for f in faces:
   vs=[int(owner[where[v]]) for v in f.vertices]
   for a,b in zip(vs,vs[1:]+vs[:1]):parents[root(a)]=root(b)
  labels=np.array([root(i) for i in owner])
  for label in np.unique(labels):
   take=np.array(ids)[labels==label];part=p[take];lo=part.min(0);hi=part.max(0);height=hi[2]-lo[2]
   rule=next((r for r in rules if height>=r['min_height_m'] and r['top_range_m'][0]<=hi[2]<=r['top_range_m'][1] and r['bottom_range_m'][0]<=lo[2]<=r['bottom_range_m'][1]),None)
   if rule is None:continue
   roots=take[part[:,2]>=hi[2]-rule['root_band_m']];reference=w[roots].mean(0)
   if rule['kind']=='skirt':
    allowed=[ni[n] for n in ['pelvis','spine','spine1']];mask=np.zeros(28);mask[allowed]=1;reference*=mask
    if reference.sum()<1e-6:reference[ni['pelvis']]=1
   reference/=reference.sum();w[take]=reference;hanging.update(take.tolist())
   reports.append(dict(material=material,kind=rule['kind'],vertices=len(take),root_vertices=len(roots),attachment_weights=reference.tolist()))
 # Source helper shoulder weights are too steep after bone collapse. Replace
 # only the measured upper skin/garment transition with a continuous field.
 sx=float(abs(source[ni['l_upperarm_twist'],0]));ez=float(source[ni['l_foretwist'],2]);sz=float(source[ni['l_upperarm_twist'],2]);nz=float(source[ni['neck'],2])
 mask=smooth(ez+.025,ez+.105,p[:,2])*(1-smooth(sz+.10,max(nz+.09,sz+.17),p[:,2]))*(1-smooth(sx*1.9,sx*2.5,abs(p[:,0])))
 allowed={int(v) for f in me.polygons if ('body' in ob.material_slots[f.material_index].material.name.lower() or 'cloth' in ob.material_slots[f.material_index].material.name.lower()) and not any(k in ob.material_slots[f.material_index].material.name.lower() for k in ['hair','eye','head']) for v in f.vertices}
 allowed-=hanging
 mask*=np.isin(np.arange(len(p)),list(allowed));field=np.zeros_like(w)
 for pre,sign in [('l',-1),('r',1)]:
  side=p[:,0]*sign>=0;t=smooth(sx*.35,sx*2.1,abs(p[:,0]));field[:,ni['spine2']]+=side*(1-t);field[:,ni[pre+'_upperarm_twist']]+=side*t
 w=w*(1-mask[:,None])+field*mask[:,None];w/=w.sum(1,keepdims=True)
 garment={int(v) for f in me.polygons if ob.material_slots[f.material_index].material.name in cfg.get('arm_rebind_materials',[]) for v in f.vertices}-hanging
 for pre in ['l','r']:
  upper=source[ni[pre+'_upperarm_twist']];elbow=source[ni[pre+'_foretwist']];wrist=source[ni[pre+'_hand']]
  direction=(wrist-upper);direction/=np.linalg.norm(direction);fore=wrist-elbow;fore/=np.linalg.norm(fore)
  band=float(np.linalg.norm(elbow-upper)*.31);wband=float(np.linalg.norm(wrist-elbow)*.29)
  te=smooth(-band,band,(p-elbow)@direction);tw=smooth(-wband,wband,(p-wrist)@fore)
  field=np.zeros_like(w);field[:,ni[pre+'_upperarm_twist']]=1-te;field[:,ni[pre+'_foretwist']]=te*(1-tw);field[:,ni[pre+'_hand']]=te*tw
  distance=np.minimum(np.linalg.norm(p-elbow,axis=1),np.linalg.norm(p-wrist,axis=1));extent=max(band,wband)
  strength=1-smooth(extent*1.25,extent*2.25,distance)
  strength*=np.isin(np.arange(len(p)),list(garment))*(p[:,0]*(-1 if pre=='l' else 1)>0)
  w=w*(1-strength[:,None])+field*strength[:,None];w/=w.sum(1,keepdims=True)
 hipwidth=float(abs(source[ni['l_thigh'],0]-source[ni['r_thigh'],0]));pz=float(source[ni['pelvis'],2])
 allowed={int(v) for f in me.polygons if ob.material_slots[f.material_index].material.name in cfg.get('pelvic_rebind_materials',[]) for v in f.vertices}
 pelvic=smooth(pz-.20,pz-.14,p[:,2])*(1-smooth(pz+.08,pz+.15,p[:,2]))*(1-smooth(hipwidth*.65,hipwidth*.95,abs(p[:,0])))*np.isin(np.arange(len(p)),list(allowed))
 t=smooth(hipwidth*.08,hipwidth*.65,abs(p[:,0]))*(1-smooth(pz-.08,pz+.06,p[:,2]));field=np.zeros_like(w);field[:,ni['pelvis']]=1-t;field[:,ni['l_thigh']]=t*(p[:,0]<0);field[:,ni['r_thigh']]=t*(p[:,0]>=0)
 w=w*(1-pelvic[:,None])+field*pelvic[:,None];w/=w.sum(1,keepdims=True)
 return w,dict(hanging_attachments=reports,shoulder_field_vertices=int((mask>0).sum()),source_dimensions_used=dict(shoulder_x_m=sx,elbow_height_m=ez,shoulder_height_m=sz,neck_height_m=nz),geometry_unchanged=True)
