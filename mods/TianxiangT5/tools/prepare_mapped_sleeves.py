"""Prepare route-2 editor inputs; does NOT cook Bannerlord mapping or publish."""
import bpy, json, hashlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'source'
mask = np.load(ROOT/'build/sleeve_mask.npz')
raw = json.loads((ROOT/'build/sleeve_baseline/meshes.json').read_text())
m = next(x for x in raw if x['name']=='tx5_body_00')
p = np.array(m['pos']); f = np.array(m['idx']).reshape(-1,3)
assert np.array_equal(p, mask['pos'])
bpy.ops.wm.open_mainfile(filepath=str(OUT/'TianxiangT5_Rigged.blend'))
rig = next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
render = bpy.data.objects['tx5_body_00']
accepted = np.array([tuple(v.co) for v in render.data.vertices])
attr = render.data.color_attributes['ClothDistance']
# Mapped render alpha is a binary mask; movement distances belong to the proxy.
for v in render.data.vertices:
    i = int(np.argmin(np.linalg.norm(p-np.array(v.co),axis=1)))
    assert np.linalg.norm(p[i]-v.co)<2e-6
    attr.data[v.index].color = (1,1,1,float(mask['streamers'][i] and mask['alpha'][i]>0))

vertices=[]; faces=[]; alpha=[]; source_indices=[]; regions=[]
for k in np.unique(mask['labels'][mask['streamers']]):
    ids=np.flatnonzero(mask['labels']==k)
    # Weld exporter seam splits, but do not merge vertices across left/right tails.
    _, reps, inv=np.unique(np.round(p[ids],5),axis=0,return_index=True,return_inverse=True)
    q=p[ids[reps]]
    index={int(old):int(new) for old,new in zip(ids,inv)}
    local=np.array([[index[int(i)] for i in tri] for tri in f if all(int(i) in index for i in tri)])
    assert all(len(set(tri))==3 for tri in local)
    assert len(np.unique(np.sort(local,axis=1),axis=0))==len(local)
    area=np.linalg.norm(np.cross(q[local[:,1]]-q[local[:,0]],q[local[:,2]]-q[local[:,0]]),axis=1)/2
    assert area.min()>1e-9
    edges=np.sort(np.concatenate([local[:,[0,1]],local[:,[1,2]],local[:,[2,0]]]),axis=1)
    _,counts=np.unique(edges,axis=0,return_counts=True)
    assert counts.max()<=2, 'Non-manifold proxy'
    a=mask['alpha'][ids[reps]]/255
    assert (a==0).sum()>=2 and (a>0).sum()>100
    for old,new in zip(ids,inv):
        assert mask['alpha'][old]==mask['alpha'][ids[reps[new]]]
    offset=len(vertices)
    vertices.extend(q.tolist()); faces.extend((local+offset).tolist()); alpha.extend(a.tolist())
    nearest=np.argmin(np.linalg.norm(q[:,None]-accepted[None],axis=2),axis=1)
    assert np.linalg.norm(q-accepted[nearest],axis=1).max()<2e-6
    source_indices.extend(nearest.tolist())
    regions.append({'side':'left' if q[:,0].mean()<0 else 'right','vertices':len(q),
                    'triangles':len(local),'fixed_vertices':int((a==0).sum()),
                    'boundary_edges':int((counts==1).sum()),'min_triangle_area_m2':float(area.min())})
assert len(regions)==2
mesh=bpy.data.meshes.new('tx5_sleeve_simulation_geometry')
mesh.from_pydata(vertices,[],faces); mesh.update()
proxy=bpy.data.objects.new('tx5_sleeve_simulation',mesh)
bpy.context.scene.collection.objects.link(proxy)
proxy.matrix_world=render.matrix_world.copy()
for group in render.vertex_groups: proxy.vertex_groups.new(name=group.name)
for i,j in enumerate(source_indices):
    groups=render.data.vertices[j].groups
    assert 1<=len(groups)<=4 and abs(sum(g.weight for g in groups)-1)<1e-5
    for g in groups: proxy.vertex_groups[g.group].add([i],g.weight,'REPLACE')
mod=proxy.modifiers.new('Native human skeleton','ARMATURE'); mod.object=rig
ca=mesh.color_attributes.new(name='ClothDistance',type='FLOAT_COLOR',domain='POINT')
for i,a in enumerate(alpha): ca.data[i].color=(1,1,1,a)
mesh.color_attributes.active_color=ca
proxy['cloth_distance_multiplier']=2.0
proxy['cloth_material']='tx5_water_sleeve'
proxy['status']='EDITOR INPUT ONLY: mapping and engine preview pending'
proxy['render_mapping_target']='tx5_body / tx5_body_00'
proxy.hide_render=True
render['cloth_route']='mapped candidate; only detached long sleeves are mapped'
render['cloth_status']='NOT COOKED: select simulation mesh and Save mesh settings in official editor'
for img in bpy.data.images:
    if img.source=='FILE': assert img.packed_file is not None, img.name
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TianxiangT5_MappedSleeves.blend'))

def export(path,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [rig]+objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','ARMATURE'},
        add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
        mesh_smooth_type='FACE',colors_type='LINEAR',use_mesh_modifiers=False)

export(OUT/'TianxiangT5_SleeveSimulation.fbx',[proxy])
render_objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o!=proxy and not o.name.endswith('_cloth_preview')]
export(OUT/'TianxiangT5_MappedSleeves_Render.fbx',render_objects)
assert np.array_equal(accepted,np.array([tuple(v.co) for v in render.data.vertices]))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'TianxiangT5_MappedSleeves.blend'))
assert len(bpy.data.objects['tx5_sleeve_simulation'].data.vertices)==len(vertices)
packed=sum(img.source=='FILE' and img.packed_file is not None for img in bpy.data.images)
assert packed==23
assert np.array_equal(accepted,np.array([tuple(v.co) for v in bpy.data.objects['tx5_body_00'].data.vertices]))
# Read back both exports and check that the simulation mask and skeleton survived.
expected=[('TianxiangT5_SleeveSimulation.fbx',1),('TianxiangT5_MappedSleeves_Render.fbx',len(render_objects))]
roundtrip=[]
for name,count in expected:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT/name))
    imported=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(imported)==count
    assert len([o for o in bpy.context.scene.objects if o.type=='ARMATURE'])==1
    for obj in imported:
        assert np.isfinite(np.array([tuple(v.co) for v in obj.data.vertices])).all()
        assert any(mod.type=='ARMATURE' for mod in obj.modifiers)
    if count==1:
        obj=imported[0]; color=obj.data.color_attributes.active_color
        assert len(obj.data.vertices)==len(vertices) and len(obj.data.polygons)==len(faces)
        assert color is not None
        alphas=np.array([c.color[3] for c in color.data])
        assert (alphas==0).sum()>0 and alphas.max()>.9
    else:
        obj=next(o for o in imported if o.name=='tx5_body_00')
        color=obj.data.color_attributes.active_color
        assert color is not None
        alphas=np.array([c.color[3] for c in color.data])
        assert set(alphas.tolist())=={0.,1.}, 'Mapped render alpha did not survive FBX'
    roundtrip.append({'file':name,'meshes':count,'passed':True})
files=['TianxiangT5_MappedSleeves.blend']+[x[0] for x in expected]
report={'status':'prepared; official editor mapping/cooking and engine preview NOT completed',
    'route':'mapped simulation','proxy_regions':regions,'proxy_vertices':len(vertices),
    'proxy_triangles':len(faces),'render_geometry_changed':False,'installed_module_changed':False,
    'fbx_roundtrip':roundtrip,'files':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in files},
    'official_solver_used':False,'distance_multiplier':2.0,'reopened_blend_packed_images':packed,
    'references':['https://moddocs.bannerlord.com/zh_cn/editor/resource-editors/cloth_simulation/',
                  'https://moddocs.bannerlord.com/asset-management/asset-types/overriding_assets/']}
(ROOT/'reports/mapped_sleeves_preparation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
