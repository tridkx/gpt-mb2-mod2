"""Model-scaled shoulder blending and attachment weights for hanging panels."""
import numpy as np
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def refine(me,ob,p,w,cfg,source,ni):
 # Collapse hanging helper chains to their actual upper attachment, rather
 # than letting a continuous skirt interpolate across independently moving legs.
 reports=[]
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
   reference/=reference.sum();w[take]=reference
   reports.append(dict(material=material,kind=rule['kind'],vertices=len(take),root_vertices=len(roots),attachment_weights=reference.tolist()))
 # Source helper shoulder weights are too steep after bone collapse. Replace
 # only the measured upper skin/garment transition with a continuous field.
 sx=float(abs(source[ni['l_upperarm_twist'],0]));ez=float(source[ni['l_foretwist'],2]);sz=float(source[ni['l_upperarm_twist'],2]);nz=float(source[ni['neck'],2])
 mask=smooth(ez+.025,ez+.105,p[:,2])*(1-smooth(sz+.055,nz+.015,p[:,2]))*(1-smooth(sx*1.9,sx*2.5,abs(p[:,0])))
 allowed={int(v) for f in me.polygons if ('body' in ob.material_slots[f.material_index].material.name.lower() or 'cloth' in ob.material_slots[f.material_index].material.name.lower()) and not any(k in ob.material_slots[f.material_index].material.name.lower() for k in ['hair','eye','head']) for v in f.vertices}
 mask*=np.isin(np.arange(len(p)),list(allowed));field=np.zeros_like(w)
 for pre,sign in [('l',-1),('r',1)]:
  side=p[:,0]*sign>=0;t=smooth(sx*.35,sx*2.1,abs(p[:,0]));field[:,ni['spine2']]+=side*(1-t);field[:,ni[pre+'_upperarm_twist']]+=side*t
 w=w*(1-mask[:,None])+field*mask[:,None];w/=w.sum(1,keepdims=True)
 return w,dict(hanging_attachments=reports,shoulder_field_vertices=int((mask>0).sum()),source_dimensions_used=dict(shoulder_x_m=sx,elbow_height_m=ez,shoulder_height_m=sz,neck_height_m=nz),geometry_unchanged=True)
