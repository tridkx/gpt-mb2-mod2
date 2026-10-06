import bpy,json,os,sys
import numpy as np
ROOT=r'D:\gpt-mb2-mod2'
sys.path.insert(0,r'D:\gpt-mb2-mod\pipeline')
from build_assets import vertex_tangents
bpy.ops.wm.open_mainfile(filepath=ROOT+'/source/TianxiangT5_Rigged.blend')
manifest=json.load(open(ROOT+'/build/rig_manifest.json'))

# Preserve the shared neck boundary in every LOD. Each equipment is simplified
# separately; collapsing either copy of this ring would reopen the seam.
neck_objects=[bpy.data.objects['tx5_body_04'],bpy.data.objects['tx5_head_11']]
point_sets=[{tuple(round(c,6) for c in v.co) for v in o.data.vertices} for o in neck_objects]
neck_points=point_sets[0]&point_sets[1]

def skin_vector(o,v):
 w=np.zeros(28)
 for g in v.groups:
  name=o.vertex_groups[g.group].name
  if name.startswith('bip01_'):w[int(name.rsplit('_',1)[1])]=g.weight
 return w

def neck_state(o):
 return {tuple(round(c,6) for c in v.co):skin_vector(o,v) for v in o.data.vertices if tuple(round(c,6) for c in v.co) in neck_points}
groups=[]
os.makedirs(ROOT+'/build/mesh',exist_ok=True)
for r in manifest:
 original=bpy.data.objects[r['object']]
 for lod,ratio in [(0,1),(1,.58),(2,.28),(3,.12)]:
  o=original.copy();o.data=original.data.copy();bpy.context.scene.collection.objects.link(o)
  for m in list(o.modifiers):o.modifiers.remove(m)
  bpy.context.view_layer.objects.active=o
  if lod:
   protected=r['object'] in {'tx5_body_04','tx5_head_11'}
   if protected:
    before=neck_state(original)
    guard=o.vertex_groups.new(name='LOD_Neck_Protection')
    center=np.array(list(neck_points));P=np.array([v.co for v in o.data.vertices])
    distance=np.linalg.norm(P[:,None,:]-center[None,:,:],axis=2).min(1)
    for vi in np.where(distance<.025)[0]:guard.add([int(vi)],1.0,'REPLACE')
   dec=o.modifiers.new('LOD','DECIMATE');dec.ratio=ratio
   if protected:dec.vertex_group=guard.name;dec.vertex_group_factor=1000
   bpy.ops.object.modifier_apply(modifier=dec.name)
   if protected:
    after=neck_state(o)
    if any(k not in after or np.max(np.abs(after[k]-w))>1e-6 for k,w in before.items()):
     # Exact attachment takes priority if the simplifier cannot retain it.
     o.data=original.data.copy();print('LOD_SEAM_FALLBACK',r['object'],lod)
    guard=o.vertex_groups.get('LOD_Neck_Protection')
    if guard:o.vertex_groups.remove(guard)
  me=o.data;me.calc_loop_triangles()
  if me.uv_layers:me.calc_tangents()
  uv=me.uv_layers.active.data
  alpha=me.color_attributes.get('ClothDistance')
  records=[];faces=[];dedup={}
  for tri in me.loop_triangles:
   inds=[]
   for li in tri.loops:
    loop=me.loops[li];vi=loop.vertex_index;v=me.vertices[vi]
    n=me.corner_normals[li].vector if hasattr(me,'corner_normals') else v.normal
    u=list(uv[li].uv);u[1]=1-u[1]
    key=(vi,tuple(round(x,6) for x in n),tuple(round(x,7) for x in u))
    if key not in dedup:
     weights=sorted([(int(g.group),float(g.weight)) for g in v.groups if g.weight>1e-6],key=lambda g:-g[1])[:4]
     idx=[int(o.vertex_groups[g].name.rsplit('_',1)[1]) for g,w in weights]
     w=np.array([w for g,w in weights]);w/=w.sum();qw=np.floor(w*255).astype(int);qw[np.argmax(w)]+=255-qw.sum()
     while len(idx)<4:idx.append(0);qw=np.append(qw,0)
     a=alpha.data[vi].color[3] if alpha and lod==0 else 0
     records.append((list(v.co),list(n),u,idx,qw.tolist(),[255,255,255,round(a*255)]))
     dedup[key]=len(records)-1
    inds.append(dedup[key])
   faces.append(inds)
  P=np.array([x[0] for x in records]);N=np.array([x[1] for x in records]);UV=np.array([x[2] for x in records]);F=np.array(faces)
  T=vertex_tangents(P,F,UV,N)
  name=r['object']+('' if not lod else '.lod'+str(lod));path=ROOT+'/build/mesh/'+name+'.mgeo'
  with open(path,'wb') as f:
   f.write(np.array([0x4F45474D,len(P),F.size],'<i4').tobytes())
   for a in [P,N,T,UV,np.zeros((len(P),2))]:f.write(np.asarray(a,'<f4').tobytes())
   for a in [[x[5] for x in records],[x[3] for x in records],[x[4] for x in records]]:f.write(np.asarray(a,'u1').tobytes())
   f.write(F.astype('<u4').tobytes())
  groups.append({'part':r['part'],'geometry':path,'material':r['material'],'name':name,'flags':[],'materialFlags':['no_team_color','no_tattoo'],'lod':lod,'tris':len(F),'vertices':len(P),'cloth':r['cloth'] and lod==0})
  bpy.data.objects.remove(o,do_unlink=True)
json.dump(groups,open(ROOT+'/build/geometry.json','w'),indent=1)
print('GEOMETRY_READY',len(groups),'groups')
