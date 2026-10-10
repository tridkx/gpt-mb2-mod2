"""Check the reported hip-support gap, packed AO channels and source dimensions."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];B=R/'build'
sys.path.insert(0,str(R.parents[1]/'tools/asset_helpers/tools'))
from georead import read_geo
cfg=json.loads((R/'tools/model_config.json').read_text())
pkg=R/'module/YueQingShuRace/AssetPackages/yqs.tpac'
caps=json.loads((R/'reports/cloth_collision.json').read_text())['capsules']
original=json.loads((R/'reports/history/v0.2.0/cloth_collision.json').read_text())['capsules']
meshes=[m for f in (B/'final_export_lod0/geo').glob('*.bin') for m in read_geo(f)]
p=np.concatenate([m['pos'] for m in meshes if m['name'].startswith('yqs_part_08')])
hip=p[(abs(p[:,0])<.155)&(p[:,2]>.87)&(p[:,2]<1.05)]
assert len(hip)>100
def clearance(points,cs):
    d=np.full(len(points),100.)
    for cap in cs:
        a,b=np.array(cap['endpoints_m']);axis=b-a;t=np.clip((points-a)@axis/(axis@axis),0,1)
        d=np.minimum(d,np.linalg.norm(points-a-t[:,None]*axis,axis=1)-cap['radius_m'])
    return d
old,new=clearance(hip,original),clearance(hip,caps)
assert np.max(new)<.01 and np.percentile(new,95)<.002
pelvis=[c for c in caps if c['name'].startswith('pelvis_')]
assert len(pelvis)==3 and all(c['bones']==['pelvis','pelvis'] for c in pelvis)
xml=ET.parse(R/'module/YueQingShuRace/ModuleData/cloth_bodies.xml').getroot()
assert len(xml.find('body/capsules'))==len(caps)
for cap,node in zip(caps,xml.find('body/capsules')):
    assert node.get('name')=='yqs_'+cap['name']
    assert all(abs(float(p.get('radius'))-cap['radius_m'])<1e-6 for p in node.findall('points/point'))
material_rows=json.loads((R/'reports/material_names.json').read_text())
visibility=json.loads((R/'reports/final_visibility.json').read_text())
for material in visibility['materials']:
    assert 'use_specular' in material['ShaderMaterialFlags']
    assert 'self_illumination' not in material['ShaderMaterialFlags']
neutral=np.array(Image.open(B/'final_export_lod0/tex/yqs_tex_1.png').convert('RGB'))
assert neutral[:,:,0].max()<3 and neutral[:,:,2].min()>250
assert 55<neutral[:,:,1].mean()<75
for material in material_rows.values():
    assert material['textures']['4']=='yqs_tex_1'
    assert 'use_specular' in material['shaderMaterialFlags']
    assert 'self_illumination' not in material['shaderMaterialFlags']
for node in ET.parse(R/'module/YueQingShuRace/ModuleData/skins.xml').findall('.//skin'):
    assert float(node.get('min_scale'))==1
troop=ET.parse(R/'module/YueQingShuRace/ModuleData/yqs_troops.xml').getroot()[0]
assert all(n.get('key')=='0'*128 for n in troop.findall('face/*'))
source=json.loads((R/'reports/source_validation.json').read_text())
assert source['source_geometry_max_error_m']==0
report=dict(status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256(pkg.read_bytes()).hexdigest(),
    pelvis_support=dict(samples=len(hip),old_coverage_within_10mm=float(np.mean(old<.01)),new_coverage_within_10mm=float(np.mean(new<.01)),max_surface_outside_support_m=float(new.max()),capsules=pelvis,scope='Rest-pose source body vertex proxy, not game solver or full continuous surface'),
    material=dict(ao_blue_min=int(neutral[:,:,2].min()),metallic_red_max=int(neutral[:,:,0].max()),gloss_green_mean=float(neutral[:,:,1].mean()),self_illumination=False,game_dark_scene_verified=False),
    dimensions=dict(source_height_m=source['source_height_m'],source_geometry_error_m=0,skin_min_scale=1,source_dimensions_preserved=True,wudu_settings_used=False,game_agent_scale_verified=False))
(R/'reports/feedback_fix_validation.json').write_text(json.dumps(report,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(9,5),layout='constrained')
for ax,column,label in zip(axes,[0,1],['Front X/Z','Side Y/Z']):
    ax.scatter(hip[:,column],hip[:,2],s=3,c='gray',alpha=.4,label='Source body')
    for cap in caps:
        if cap['name'] not in ['waist','l_thigh','r_thigh'] and not cap['name'].startswith('pelvis_'):continue
        a,b=np.array(cap['endpoints_m']);radius=cap['radius_m'];axis=b-a;axis/=np.linalg.norm(axis)
        # Project the capsule silhouette as its swept circles; this is a proxy.
        from matplotlib.patches import Circle
        color='tab:orange' if cap['name'].startswith('pelvis_') else 'tab:blue'
        for t in np.linspace(0,1,12):
            center=a+(b-a)*t;ax.add_patch(Circle((center[column],center[2]),radius,color=color,alpha=.045))
    ax.set(xlim=(-.20,.23),ylim=(.78,1.20),aspect='equal',title=label,xlabel='Meters',ylabel='Z (meters)')
    ax.grid(alpha=.2)
fig.suptitle('Pelvis support proxy: blue = previous, orange = added\nSource geometry unchanged; not game cloth simulation')
fig.savefig(R/'reports/pelvis_support.png',dpi=160);plt.close(fig)
print('FEEDBACK_FIXES_CHECKED',report)
