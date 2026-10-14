"""Preserve PMX shape/UV/normals and remap source skinning to custom human bind."""
import bpy,json,sys
from pathlib import Path
import numpy as np
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);B=R/'build';C=json.loads((R/'tools/model_config.json').read_text())
sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.skeleton import parse_skeljson
raw=json.loads((R/'reports/human_skeleton.json').read_text());rig=parse_skeljson(raw)
src=json.loads((B/'source_bones.json').read_text(encoding='utf8'));idx={b['name']:i for i,b in enumerate(src)};a=np.load(B/'raw_model.npz');rot=np.array(C['source_rotation']);scale=C['unit_scale']
p=a['p']@rot.T*scale;p[:,2]-=a['p'][:,1].min()*scale;n=a['n']@rot.T
def joint(name):
 q=np.array(src[idx[name]]['position'])@rot.T*scale;q[2]-=a['p'][:,1].min()*scale;return q
S=rig['restWorld'][:,:3,3].copy();S[0]=joint('下半身');S[9]=joint('上半身');S[11]=joint('上半身2');S[10]=(S[9]+S[11])/2;S[12]=joint('首');S[13]=joint('頭')
if '上半身3' in idx:S[10]=joint('上半身3')
for sign,side,ids in [('左','l',[1,2,3,4,14,15,16,17,18,19,20]),('右','r',[5,6,7,8,21,22,23,24,25,26,27])]:
 for k,bone in zip(ids[:4],['足','ひざ','足首','つま先']):S[k]=joint(sign+bone)
 clav,upper,twist,fore,ftwist,hand,finger=ids[4:];S[clav]=joint(sign+'肩');S[upper]=joint(sign+'腕');S[fore]=joint(sign+'ひじ');S[hand]=joint(sign+'手首');S[twist]=(S[upper]+S[fore])/2;S[ftwist]=(S[fore]+S[hand])/2;S[finger]=joint(sign+'親指１')
world=rig['restWorld'].copy();world[:,:3,3]=S;align=[]
for i,start,end in [(15,15,17),(16,15,17),(17,17,19),(18,17,19),(22,22,24),(23,22,24),(24,24,26),(25,24,26)]:
 u=world[i,:3,0].copy();u/=np.linalg.norm(u);v=S[end]-S[start];v/=np.linalg.norm(v);cross=np.cross(u,v);c=float(u@v);assert c>-.99;K=np.array([[0,-cross[2],cross[1]],[cross[2],0,-cross[0]],[-cross[1],cross[0],0]]);Q=np.eye(3)+K+K@K/(1+c);world[i,:3,:3]=Q@world[i,:3,:3];align.append({'bone':rig['names'][i],'degrees':float(np.degrees(np.arccos(np.clip(c,-1,1))))})
local=np.array([world[i] if par<0 else np.linalg.inv(world[par])@world[i] for i,par in enumerate(rig['parent'])]);bones=[dict(name=b['name'],parent=b['parent'],rest=local[i].T.ravel().tolist()) for i,b in enumerate(raw['bones'])];(B/'skeleton_spec.json').write_text(json.dumps(bones,indent=2))
mapping={'下半身':0,'腰':0,'上半身':9,'上半身1':9,'上半身3':10,'上半身2':11,'首':12,'頭':13,'胸饰':11,'おっぱい調整':11}
for sign,base,leg in [('左',14,1),('右',21,5)]:
 mapping.update({sign+'肩':base,sign+'肩P':base,sign+'肩C':base+1,sign+'腕':base+1,sign+'腕捩':base+2,sign+'腕捩1':base+1,sign+'腕捩2':base+2,sign+'腕捩3':base+2,sign+'ひじ':base+3,sign+'手捩':base+4,sign+'手捩1':base+3,sign+'手捩2':base+4,sign+'手捩3':base+4,sign+'手首':base+5,sign+'袖1':base+4,sign+'足':leg,sign+'足D':leg,sign+'ひざ':leg+1,sign+'ひざD':leg+1,sign+'足首':leg+2,sign+'足首D':leg+2,sign+'つま先':leg+3,sign+'足先EX':leg+3})
 for b in src:
  if b['name'].startswith(sign+'胸'):mapping[b['name']]=11
  if b['name'].startswith(sign) and any(f in b['name'] for f in ['親指','人指','中指','薬指','小指']):mapping[b['name']]=base+5
mapped=[]
for i,b in enumerate(src):
 j=i;seen=set()
 while src[j]['name'] not in mapping and src[j]['parent']>=0:
  assert j not in seen;seen.add(j);j=src[j]['parent']
 mapped.append(mapping.get(src[j]['name'],0))
w=np.zeros((len(p),28))
for k in range(4):np.add.at(w,(np.arange(len(p)),np.array(mapped)[a['bi'][:,k]]),a['bw'][:,k])
# Source Q/QB skirt chains are physics references, not native leg animation.
# Blend their contribution continuously toward thighs without changing shape.
skirt=np.array([b['name'].startswith('Q_') or 'QB_' in b['name'] or '裙' in b['name'] or 'skirt' in b['name'].lower() for b in src]);amount=(a['bw']*skirt[a['bi']]).sum(1)
z=p[:,2];pelvis_z=S[0,2];knee_z=(S[2,2]+S[6,2])/2;legmix=np.clip((pelvis_z-z)/(pelvis_z-knee_z),0,.72);side=np.clip((p[:,0]+.055)/.11,0,1);sk=np.zeros_like(w);sk[:,0]=1-legmix;sk[:,1]=legmix*(1-side);sk[:,5]=legmix*side
for i in np.flatnonzero(amount>0):w[i,0]-=amount[i];w[i]+=sk[i]*amount[i]
w=np.maximum(w,0);w/=w.sum(1,keepdims=True)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
refinements=[]
if C.get('weight_refinement',{}).get('waist',False):
 influence=w[:,[0,9,10,11]].sum(1);lo=S[0,2]-.06;hi=S[10,2]+.09;mask=(influence>.85)&(p[:,2]>lo)&(p[:,2]<hi);ids=np.flatnonzero(mask)
 if len(ids):
  amount=smooth(S[0,2]-.04,S[11,2]+.03,p[ids,2]);target=np.zeros((len(ids),28));target[:,0]=1-amount;target[:,11]=amount;fade=smooth(lo,S[0,2]-.02,p[ids,2])*(1-smooth(S[10,2]+.03,hi,p[ids,2]))*smooth(.85,1,influence[ids]);w[ids]=w[ids]*(1-fade[:,None])+target*fade[:,None];refinements.append({'region':'waist','vertices':len(ids),'vertical_band_m':[float(lo),float(hi)]})
if C.get('weight_refinement',{}).get('shoulders',False):
 region=np.zeros(len(p),bool)
 for group in json.loads((B/'source_groups.json').read_text(encoding='utf8')):
  if group['source_material_index'] in C.get('shoulder_materials',[]):region[np.unique(np.array(group['faces']))]=True
 for side,clav,upper,fore in [('l',14,15,17),('r',21,22,24)]:
  sign=-1 if side=='l' else 1;x=p[:,0]*sign;root_x=abs(S[upper,0]);arm_ids=list(range(clav,clav+7));dz=p[:,2]-S[upper,2];dy=p[:,1]-S[upper,1];style=C.get('shoulder_style','arm_only')
  if style=='arm_only':
   influence=w[:,arm_ids].sum(1);mask=(influence>1e-6)&(x>root_x*.25)&(x<root_x*1.8)&(dz>-.25)&(dz<.20)
  else:
   influence=w[:,arm_ids+[0,9,10,11]].sum(1);depth=.18 if style=='field_narrow' else .30;mask=(influence>.85)&(x>root_x*.25)&(x<root_x*1.8)&(dz>-.20)&(dz<.20)&(abs(dy)<depth)
   if style!='field_narrow':mask&=region
  ids=np.flatnonzero(mask)
  if len(ids):
   amount=smooth(root_x*.4,root_x*1.6,x[ids]);target=np.zeros((len(ids),28));target[:,11]=1-amount;target[:,upper]=amount;fade=smooth(root_x*.25,root_x*.45,x[ids])*(1-smooth(root_x*1.5,root_x*1.8,x[ids]))*(1-smooth(.10,.20,dz[ids]))
   if style=='arm_only':fade*=smooth(-.25,-.14,dz[ids])*smooth(0,.15,influence[ids])
   else:fade*=smooth(-.20,-.10,dz[ids])*(1-smooth(depth-.08,depth,abs(dy[ids])))*smooth(.85,1,influence[ids])
   w[ids]=w[ids]*(1-fade[:,None])+target*fade[:,None];refinements.append({'region':side+'_shoulder','style':style,'vertices':len(ids),'inner_x_m':root_x*.4,'outer_x_m':root_x*1.6})
 # Distal clothing was often weighted to the MMD shoulder controller. The
 # native clavicle is a different anatomical segment; move its distal share
 # onto the corresponding upper arm instead of retaining a hard clavicle seam.
 if C.get('shoulder_style','arm_only')!='arm_only':
  for clav,upper in [(14,15),(21,22)]:
   move=smooth(abs(S[upper,0])*.8,abs(S[upper,0])*1.2,abs(p[:,0]))*w[:,clav];w[:,clav]-=move;w[:,upper]+=move
if C.get('weight_refinement',{}).get('crotch',False):
 drop=S[0,2]-p[:,2];leg=w[:,[1,5]].sum(1);half_width=float((abs(S[1,0])+abs(S[5,0]))/2);outer_width=C.get('crotch_outer_width_multiplier',1.4);depth=C.get('crotch_depth_m',.20);mask=(leg>.02)&(drop>0)&(drop<depth)&(abs(p[:,0])<half_width*outer_width);ids=np.flatnonzero(mask)
 if len(ids):
  outer=smooth(half_width*.25,half_width*C.get('crotch_lateral_transition_multiplier',1.1),abs(p[ids,0]));amount=smooth(.02,.17,drop[ids])*outer;side=smooth(-half_width*.8,half_width*.8,p[ids,0]);target=np.zeros((len(ids),28));target[:,0]=1-amount;target[:,1]=amount*(1-side);target[:,5]=amount*side;fade=(1-smooth(depth*.8,depth,drop[ids]))*(1-smooth(half_width*(outer_width-.25),half_width*outer_width,abs(p[ids,0])));w[ids]=w[ids]*(1-fade[:,None])+target*fade[:,None];refinements.append({'region':'crotch','vertices':len(ids),'derived_hip_half_width_m':half_width})
(R/'reports/weight_refinement.json').write_text(json.dumps({'model':C['id'],'regions':refinements,'geometry_unchanged':True},indent=2))
# Exact source coincidences receive common weights for face/neck/material cuts.
q,owner=np.unique(np.round(p,6),axis=0,return_inverse=True);avg=np.zeros((len(q),28));np.add.at(avg,owner,w);avg/=np.bincount(owner)[:,None];w=avg[owner];keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,1);w*=mask;w/=w.sum(1,keepdims=True)
bpy.ops.wm.read_factory_settings(use_empty=True);materials=json.loads((R/'tex/materials.json').read_text(encoding='utf8'));bm={}
for key,info in materials.items():
 mat=bpy.data.materials.new('emilie_'+key);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.75;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');im=bpy.data.images.load(str(R/'tex'/info['diffuse']),check_existing=True);im.pack();tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 if info['cutout']:mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
 bm[key]=mat
manifest=[];arrays={};cloth_rows=[]
for rec in json.loads((B/'source_groups.json').read_text(encoding='utf8')):
 fs=np.array(rec.pop('faces'));ix=np.unique(fs);remap=np.full(len(p),-1,int);remap[ix]=np.arange(len(ix));faces=remap[fs];points=p[ix];weights=w[ix].copy();kind=rec['kind'];alpha=np.zeros(len(ix))
 if kind=='hair':weights[:]=0;weights[:,13]=1
 elif rec['source_material_index'] in C.get('head_materials',[]):
  invalid=(weights[:,:12].sum(1)>.5)&(points[:,2]>S[12,2]+.02)
  weights[invalid]=0;weights[invalid,13]=1
 if str(rec['source_material_index']) in C.get('rigid_material_bindings',{}):
  weights[:]=0;weights[:,C['rigid_material_bindings'][str(rec['source_material_index'])]]=1
 if rec['source_material_index'] in C.get('arm_material_bindings',[]):
  parent=list(range(len(points)))
  def find(x):
   while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
   return x
  for tri in faces:
   for vi in tri[1:]:parent[find(int(vi))]=find(int(tri[0]))
  components={}
  for vi in range(len(points)):components.setdefault(find(vi),[]).append(vi)
  for vertices in components.values():
   left=weights[vertices,14:21].sum();right=weights[vertices,21:28].sum();owner=15 if left>right else 22 if right>left else (15 if points[vertices,0].mean()<0 else 22);weights[vertices]=0;weights[vertices,owner]=1
 if rec.get('cloth'):
  # All cloth retains its real attachment owner, never the nearest leg.
  weights[:]=0;weights[:,13]=1
  policy=C['cloth_parts'][str(rec['source_material_index'])]
  top=policy['fixed_above_source_y']*scale-a['p'][:,1].min()*scale
  alpha=np.minimum(np.maximum(top-points[:,2],0)*policy.get('travel_slope',.3),policy['max_distance_m'])
  if policy.get('source_z_min') is not None:alpha[a['p'][ix,2]<policy['source_z_min']]=0
  alpha[alpha<.008]=0
  blend=np.clip((S[13,2]-points[:,2]-.12)/.35,0,C.get('hair_reference_body_blend_max',.7))
  blend[alpha==0]=0;weights[:,13]=1-blend;weights[:,11]=blend
  rec['cloth']=True
 else:rec['cloth']=False
 me=bpy.data.meshes.new(rec['object']);me.from_pydata(points.tolist(),[],faces.tolist());me.update();uv=me.uv_layers.new(name='UVMap')
 loop_ix=np.array([loop.vertex_index for loop in me.loops]);uv_values=a['uv'][ix[loop_ix]].copy();uv_values[:,1]=1-uv_values[:,1];uv.data.foreach_set('uv',uv_values.ravel())
 me.polygons.foreach_set('use_smooth',np.ones(len(me.polygons),bool))
 me.normals_split_custom_set_from_vertices(n[ix].tolist());me.materials.append(bm[rec['material']]);o=bpy.data.objects.new(rec['object'],me);bpy.context.collection.objects.link(o)
 for j,name in enumerate(rig['names']):
  g=o.vertex_groups.new(name=name+'_'+str(j))
  selected=np.flatnonzero(weights[:,j]>1e-7)
  values=np.round(weights[selected,j],5)
  for value in np.unique(values):g.add(selected[values==value].tolist(),float(value),'REPLACE')
 layer=me.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
 colors=np.ones((len(ix),4));colors[:,3]=alpha;layer.data.foreach_set('color',colors.ravel())
 rec.update(source_vertex_indices=ix.tolist());manifest.append(rec);arrays[rec['object']+'_p']=points;arrays[rec['object']+'_w']=weights;arrays[rec['object']+'_f']=faces;arrays[rec['object']+'_alpha']=alpha
 if rec['cloth']:cloth_rows.append({'object':rec['object'],'kind':kind,'vertices':len(ix),'active_vertices':int((alpha>0).sum()),'max_distance_m':float(alpha.max()),'skirt':False})
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name=C['skeleton'];bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0]);names=[name+'_'+str(i) for i,name in enumerate(rig['names'])]
for i,name in enumerate(names):b=arm.data.edit_bones.new(name);b.matrix=Matrix(world[i].tolist());b.length=.035
for i,name in enumerate(names):
 if rig['parent'][i]>=0:arm.data.edit_bones[name].parent=arm.data.edit_bones[names[rig['parent'][i]]]
bpy.ops.object.mode_set(mode='OBJECT')
for rec in manifest:o=bpy.data.objects[rec['object']];mod=o.modifiers.new('Race binding','ARMATURE');mod.object=arm;o.parent=arm
(B/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');np.savez_compressed(B/'fitted_model.npz',**arrays)
(R/'reports/weight_transfer.json').write_text(json.dumps({'source_proportions_preserved':True,'uniform_scale':scale,'source_rotation':rot.tolist(),'native_bones':rig['names'],'source_landmarks':S.tolist(),'source_min_z_m':float(p[:,2].min()),'source_height_m':float(np.ptp(p[:,2])),'source_bone_mapping':dict(zip([b['name'] for b in src],mapped)),'skirt_cloth_enabled':False},ensure_ascii=False,indent=2),encoding='utf8')
(R/'reports/arm_bind_alignment.json').write_text(json.dumps({'enabled':True,'bones':align},indent=2));(R/'reports/cloth_paint.json').write_text(json.dumps(cloth_rows,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/EmilieRace_Rigged.blend'));bpy.ops.export_scene.fbx(filepath=str(R/'source/EmilieRace_Rigged.fbx'),object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,path_mode='COPY',embed_textures=True)
print('SOURCE_READY',len(manifest),'parts',len(cloth_rows),'cloth groups',np.ptp(p[:,2]),'metres')
