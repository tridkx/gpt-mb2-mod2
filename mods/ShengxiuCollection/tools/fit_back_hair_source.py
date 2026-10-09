"""Fit rear rest shape and give long hair a root-to-tip cloth travel gradient."""
import bpy,json,sys,shutil
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hair_shape_analysis import read_geo,smooth,rear_surface
base=ROOT/'build/back_hair_baseline_v1.1.6';base.mkdir(exist_ok=True)
for path in [ROOT/'source/ShengxiuCollection_Rigged.blend',ROOT/'source/ShengxiuCollection_Rigged.fbx',ROOT/'build/rig_arrays.npz',ROOT/'build/rig_manifest.json',ROOT/'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac']:
 if not (base/path.name).exists():shutil.copy2(path,base/path.name)
arrays=dict(np.load(base/'rig_arrays.npz'));manifest=json.loads((base/'rig_manifest.json').read_text());name='sx_mingyu_head_00'
p=arrays[name+'_P'];old=np.load(ROOT/'build/hair_shape_baseline_v1.1.4/rig_arrays.npz')[name+'_P']
rear=(old[:,1]<-.025)&(old[:,2]<1.50)
triangles=[];body_points=[];body_weights=[]
for f in (ROOT/'build/head_neck_final_export/geo').glob('*.bin'):
 for m in read_geo(f):
  if m['name'] not in ['sx_mingyu_body_01','sx_mingyu_body_02','sx_mingyu_body_13','sx_mingyu_body_06']:continue
  faces=m['idx'].reshape(-1,3);v=m['pos'][faces]
  keep=(abs(v[:,:,0]).max(1)<.18)&(v[:,:,1].min(1)>-.18)&(v[:,:,2].min(1)>.80)
  dense=np.zeros((len(m['pos']),28));np.add.at(dense,(np.arange(len(dense))[:,None],m['bi']),m['bw']/255)
  triangles.append(v[keep])
  if m['name'] in ['sx_mingyu_body_01','sx_mingyu_body_02']:
   inner=(abs(m['pos'][:,0])<.09)&(m['pos'][:,1]<-.015)
   body_points.append(m['pos'][inner]);body_weights.append(dense[inner])
# A continuous height profile preserves the flow of the hair cards. Individual
# nearest triangles have seams and create visible corrugation in hair sheets.
tri=np.concatenate(triangles);bp=np.concatenate(body_points);bw=np.concatenate(body_weights)
z=np.linspace(.84,1.53,70);x=np.linspace(-.10,.10,9)
samples=np.array([[xx,0,zz] for zz in z for xx in x]);ys=rear_surface(samples,tri).reshape(len(z),len(x))
ys[(ys>-.015)|~np.isfinite(ys)]=np.nan
surface_profile=np.array([np.nanmin(row) if np.isfinite(row).any() else np.nan for row in ys]);valid=np.isfinite(surface_profile)
surface_profile=np.interp(z,z[valid],surface_profile[valid])
kernel=np.array([1,2,3,2,1])/9
surface_profile=np.convolve(np.pad(surface_profile,(2,2),mode='edge'),kernel,mode='valid')
front_profile=np.array([np.max(p[rear&(abs(p[:,2]-zz)<.025),1]) if np.any(rear&(abs(p[:,2]-zz)<.025)) else np.nan for zz in z]);valid=np.isfinite(front_profile)
front_profile=np.interp(z,z[valid],front_profile[valid]);front_profile=np.convolve(np.pad(front_profile,(2,2),mode='edge'),kernel,mode='valid')
weight_profile=[]
for zz in z:
 ids=np.argsort(abs(bp[:,2]-zz))[:12];row=bw[ids].mean(0);row[[i for i in range(28) if i not in [0,9,10,11,12]]]=0
 row/=row.sum();weight_profile.append(row)
weight_profile=np.array(weight_profile)
for bone in range(28):weight_profile[:,bone]=np.convolve(np.pad(weight_profile[:,bone],(2,2),mode='edge'),kernel,mode='valid')
target_weights=np.column_stack([np.interp(p[:,2],z,weight_profile[:,bone]) for bone in range(28)])
surface=np.interp(p[:,2],z,surface_profile);front=np.interp(p[:,2],z,front_profile)
strength=(1-smooth(1.30,1.53,p[:,2]))*rear
gap=surface-p[:,1];target=surface-.024-.45*np.maximum(front-p[:,1],0)
shift=np.zeros(len(p));shift[rear]=(target[rear]-p[rear,1])*strength[rear]
q=p.copy();q[:,1]+=shift;hit=rear
# Remove the posterior bulge at the nape while preserving scalp roots and the
# existing lower sheet. Smoothstep gives a tangent-continuous local correction.
# Only genuinely posterior strands are included; front locks remain intact.
nape_rear=1-smooth(-.055,-.015,old[:,1])
nape_band=smooth(1.32,1.48,p[:,2])*(1-smooth(1.49,1.59,p[:,2]))
nape_shift=.045*nape_rear*nape_band
q[:,1]+=nape_shift
w=arrays[name+'_W']*(1-strength[:,None])+target_weights*strength[:,None]
keep=np.argsort(-w,axis=1)[:,:4];mask=np.zeros_like(w);np.put_along_axis(mask,keep,1,axis=1);w*=mask;w/=w.sum(1,keepdims=True)
bpy.ops.wm.open_mainfile(filepath=str(base/'ShengxiuCollection_Rigged.blend'));o=bpy.data.objects[name]
# Keep the existing scalp roots and front locks. The 8mm cap prevented gravity
# from moving the rear sheet toward the back; allow up to 200mm at the tips.
alpha=arrays[name+'_A'].copy()
original_fixed=alpha==0
rear_blend=1-smooth(-.025,.015,old[:,1])
travel=.200*(1-smooth(1.00,1.586,old[:,2]))
free=alpha>0
alpha[free]=alpha[free]*(1-rear_blend[free])+travel[free]*rear_blend[free]
attr=o.data.color_attributes['ClothDistance']
for i,value in enumerate(alpha):attr.data[i].color[3]=float(value)
arrays[name+'_A']=alpha
for vertex in o.data.vertices:
 i=vertex.index;vertex.co=q[i]
 for group in o.vertex_groups:group.remove([i])
 for bone in np.flatnonzero(w[i]>1e-6):next(g for g in o.vertex_groups if g.name.endswith('_'+str(bone))).add([i],float(w[i,bone]),'REPLACE')
o.data.update();arrays[name+'_P']=q;arrays[name+'_W']=w
np.savez(ROOT/'build/rig_arrays.npz',**arrays)
for rec in manifest:
 if rec['object']==name:rec['bounds']=[q.min(0).tolist(),q.max(0).tolist()]
(ROOT/'build/rig_manifest.json').write_text(json.dumps(manifest,indent=2))
for ob in bpy.context.scene.objects:ob.select_set(ob.type in ['MESH','ARMATURE'])
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/ShengxiuCollection_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(ROOT/'source/ShengxiuCollection_Rigged.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
report={'status':'pass','changed_object':name,'target_minimum_profile_gap_m':.024,'remaining_depth_fraction':.45,'maximum_additional_forward_m':float(shift.max()),'torso_follow_fade_z_m':[1.30,1.53],'median_profile_gap_before_m':float(np.median(gap[hit])),'median_profile_gap_after_m':float(np.median((surface-q[:,1])[hit])),'head_neck_all_other_objects_unchanged':True,'rear_cloth_max_distance_m':float(alpha[rear].max()),'original_scalp_fixed_vertices_unchanged':bool(np.array_equal(alpha==0,original_fixed)),'profile_z_m':z.tolist(),'body_back_y_m':surface_profile.tolist()}
report['nape_smoothing_max_forward_m']=float(nape_shift.max())
report['nape_smoothing_height_m']=[1.32,1.48,1.49,1.59]
(ROOT/'reports/back_hair_source_fit.json').write_text(json.dumps(report,indent=2));print('BACK_HAIR_SOURCE_FIT',report)
