from workspace_paths import workspace_root
"""Cook current mesh topology and author source-proportioned cloth capsules."""
import json,sys,subprocess,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from pelvis_support import surface_samples
R=Path(__file__).resolve().parents[1];WS=workspace_root(R);B=R/'build';C=WS/'tools/cloth_compiler'
def run(args):subprocess.run([str(x) for x in args],check=True)
transfer=json.loads((R/'reports/weight_transfer.json').read_text());names=transfer['native_bones'];p=np.array(transfer['source_landmarks']);at=lambda name:p[names.index(name)]
caps=[]
def cap(name,a,b,r,ba,bb):caps.append((name,np.array(a),np.array(b),r,ba,bb))
# These radii are specific to this source: no native adult collision body.
cap('waist',[0,.080,1.00],[0,.082,1.15],.067,'spine','spine1')
# Fit the complete surface, including side and lower edges, not percentiles.
# Collision skin must surround the body; the former positive 10 mm tolerance
# left visible body outside the support. Keep a 6 mm fabric clearance.
source=np.load(B/'fitted_model.npz');body_p=source['yqs_part_08_p']
hip=surface_samples(body_p,source['yqs_part_08_f'],4)
assert len(hip)>100
xs=np.array([-.055,0,.055]);assigned=np.argmin(np.abs(hip[:,0,None]-xs),axis=1)
for index,x in enumerate(xs):
    section=hip[assigned==index];cy=float((section[:,1].min()+section[:,1].max())/2)
    a=np.array([x,cy,.84]);b=np.array([x,cy,1.08]);axis=b-a
    t=np.clip((section-a)@axis/(axis@axis),0,1)
    radius=float(np.linalg.norm(section-a-t[:,None]*axis,axis=1).max()+.006)
    assert .08<radius<.13
    cap('pelvis_'+str(x),a,b,radius,'pelvis','pelvis')
for x in [-.045,0,.045]:cap('back_'+str(x),[x,.060,1.17],[x,.058,1.36],.045,'spine1','spine2')
cap('neck',[0,.039,1.39],[0,.047,1.46],.030,'spine2','neck')
cap('head',[0,.065,1.48],[0,.065,1.59],.060,'head','head')
for pre in ['l','r']:
    thigh=at(pre+'_thigh');calf=at(pre+'_calf');foot=at(pre+'_foot')
    axis=calf-thigh
    cap(pre+'_thigh',thigh+.08*axis,calf-.08*axis,.059,pre+'_thigh',pre+'_calf')
    cap(pre+'_calf',calf+.06*(foot-calf),foot,.043,pre+'_calf',pre+'_foot')
    cap(pre+'_upperarm',at(pre+'_upperarm_twist'),at(pre+'_foretwist'),.027,pre+'_upperarm_twist',pre+'_foretwist')
    cap(pre+'_forearm',at(pre+'_foretwist'),at(pre+'_hand'),.022,pre+'_foretwist',pre+'_hand')
root=ET.Element('bodies');body=ET.SubElement(root,'body',name='yqs_collision',owner_skeleton='yqs_skeleton');container=ET.SubElement(body,'capsules');rows=[]
for name,a,b,radius,ba,bb in caps:
    u=b-a;length=np.linalg.norm(u);u/=length;v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);t=np.cross(v,u)
    frame=np.eye(4);frame[:3,:3]=[u,t,v];frame[3,:3]=a
    capsule=ET.SubElement(container,'capsule',name='yqs_'+name,length=f'{length:.6f}',origin='0, 0, 0',frame=', '.join(f'{x:.6f}' for x in frame.ravel()))
    points=ET.SubElement(capsule,'points')
    for bone in [ba,bb]:
        point=ET.SubElement(points,'point',radius=f'{radius:.6f}');bones=ET.SubElement(point,'bones');ET.SubElement(bones,'bone',name=bone,weight='1.0')
    rows.append(dict(name=name,endpoints_m=[a.tolist(),b.tolist()],radius_m=radius,bones=[ba,bb]))
ET.indent(root,space='  ');ET.ElementTree(root).write(R/'module/YueQingShuRace/ModuleData/cloth_bodies.xml',encoding='utf-8',xml_declaration=True)
(R/'reports/cloth_collision.json').write_text(json.dumps(dict(capsules=rows,engine_verified=False),indent=2))
print('COLLISIONS_READY',len(caps),'source-sized capsules')
if '--collision-only' in sys.argv:sys.exit(0)

for project,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch')]:
    run(['dotnet','build',C/(project+'.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(B/'cloth_obj'/project)+'/', '-o',B/folder])
for name in ['cloth_inputs','cooked_cloth']:
    folder=(B/name).resolve();assert folder.parent==B.resolve()
    if folder.exists():shutil.rmtree(folder)
(B/'cloth_inputs').mkdir()
probe=subprocess.run(['dotnet',str(B/'cloth_probe/NativeClothProbe.dll'),str(B/'uncooked.tpac'),'yqs_body','--dump-segments',str(B/'cloth_inputs')],check=True,capture_output=True,text=True)
(R/'reports/cloth_uncooked.json').write_text(probe.stdout)
meshes=[json.loads(p.read_text()) for p in (B/'cloth_inputs').glob('*.mesh.json')]
assert meshes and {m['lod'] for m in meshes}=={0,1,2,3}
policy={'default':{'unanchored':'error'},'meshes':{}}
for mesh in meshes:
    # Source paintings contain real roots. Reduction or package splitting can
    # truncate a card; retain its surviving upper edge as the recorded root.
    if mesh['name'].startswith(('yqs_part_00','yqs_part_10','yqs_part_11')):
        policy['meshes'][mesh['name']]={'unanchored':'pin_upper','axis':2,'band_m':.008,'min_vertices':2,'reason':'Restore surviving upper attachment edge of reduced source hair, skirt/ribbon or tassel component'}
(R/'tools/cloth_policy.json').write_text(json.dumps(policy,indent=2))
run([sys.executable,C/'cook_cloth.py',B/'cloth_inputs',B/'cooked_cloth','--policy',R/'tools/cloth_policy.json'])
run(['dotnet',B/'cloth_patch/ClothPatch.dll',B/'uncooked.tpac',B/'cooked_cloth/manifest.json',R/'module/YueQingShuRace/AssetPackages/yqs.tpac','--allow-metameshes','yqs_body'])

print('CLOTH_READY',len(meshes),'cooked meshes')
