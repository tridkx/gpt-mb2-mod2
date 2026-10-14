"""Author this source's capsules and cook topology-specific direct baselines."""
import json,sys,subprocess,xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];B=R/'build';W=workspace_root(R);C=W/'tools/cloth_compiler';cfg=json.loads((R/'tools/model_config.json').read_text());p=np.array(cfg['landmarks_m']);names=json.loads((R/'reports/human_skeleton.json').read_text())['bones'];names=[b['name'] for b in names]
def run(args):subprocess.run([str(x) for x in args],check=True)
caps=[]
def cap(name,a,b,r,ba,bb):caps.append(dict(name=name,endpoints_m=[list(a),list(b)],radius_m=r,bones=[ba,bb]))
cap('pelvis',[0,-.028,.98],[0,-.027,1.05],.085,'pelvis','pelvis')
cap('torso',[0,-.030,1.14],[0,-.033,1.30],.075,'spine','spine2')
cap('head',[0,-.025,1.49],[0,-.025,1.57],.065,'head','head')
for pre in ['l','r']:
 for a,b,r,n in [('thigh','calf',.06,'thigh'),('calf','foot',.038,'calf'),('upperarm_twist','foretwist',.032,'upperarm'),('foretwist','hand',.027,'forearm')]:
  ia,ib=names.index(pre+'_'+a),names.index(pre+'_'+b);u=p[ib]-p[ia];cap(pre+'_'+n,p[ia]+u*.07,p[ib]-u*.07,r,pre+'_'+a,pre+'_'+b)
root=ET.Element('bodies');body=ET.SubElement(root,'body',name='bql_collision',owner_skeleton='bql_skeleton');container=ET.SubElement(body,'capsules')
for row in caps:
 a,b=np.array(row['endpoints_m']);u=b-a;length=np.linalg.norm(u);u/=length;v=np.cross(u,[1,0,0] if abs(u[1])>.9 else [0,1,0]);v/=np.linalg.norm(v);t=np.cross(v,u);frame=np.eye(4);frame[:3,:3]=[u,t,v];frame[3,:3]=a
 node=ET.SubElement(container,'capsule',name='bql_'+row['name'],length=f'{length:.6f}',origin='0, 0, 0',frame=', '.join(f'{x:.6f}' for x in frame.ravel()));points=ET.SubElement(node,'points')
 for name in row['bones']:point=ET.SubElement(points,'point',radius=f"{row['radius_m']:.6f}");bn=ET.SubElement(point,'bones');ET.SubElement(bn,'bone',name=name,weight='1.0')
ET.indent(root,space='  ');ET.ElementTree(root).write(R/'module'/cfg['id']/'ModuleData/cloth_bodies.xml',encoding='utf-8',xml_declaration=True);(R/'reports/cloth_collision.json').write_text(json.dumps(dict(capsules=caps,game_verified=False),indent=2))
for project,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch')]:run(['dotnet','build',C/(project+'.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(B/'cloth_obj'/project)+'/','-o',B/folder])
(B/'cloth_inputs').mkdir(exist_ok=True)
run(['dotnet',B/'cloth_probe/NativeClothProbe.dll',B/'uncooked.tpac','bql_body','--dump-segments',B/'cloth_inputs'])
meshes=[json.loads(f.read_text()) for f in (B/'cloth_inputs').glob('*.mesh.json')];assert {m['lod'] for m in meshes}=={0,1}
# Detached cloth panels and thin hair cards retain their own highest attachment.
policy=dict(default=dict(unanchored='error'),meshes={m['name']:dict(unanchored='pin_upper',axis=2,band_m=.012,min_vertices=2,reason='Preserve highest surviving attachment of this source panel/card') for m in meshes})
(R/'tools/cloth_policy.json').write_text(json.dumps(policy,indent=2));run([sys.executable,C/'cook_cloth.py',B/'cloth_inputs',B/'cooked_cloth','--policy',R/'tools/cloth_policy.json'])
run(['dotnet',B/'cloth_patch/ClothPatch.dll',B/'uncooked.tpac',B/'cooked_cloth/manifest.json',B/'mapped_baseline_direct.tpac','--allow-metameshes','bql_body'])
(B/'cloth_final').mkdir(exist_ok=True);run(['dotnet',B/'cloth_probe/NativeClothProbe.dll',B/'mapped_baseline_direct.tpac','bql_body','--dump-segments',B/'cloth_final'])
