"""Cook only this race's cloth and write its skeleton-sized collision capsules."""
import json,sys,subprocess,shutil,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build';C=WS/'tools/cloth_compiler'
cfg=json.loads((R/'tools/model_config.json').read_text());K=cfg['unit_scale']/.01
def run(args):subprocess.run([str(x) for x in args],check=True)
for project,folder in [('NativeClothProbe','cloth_probe'),('ClothPatch','cloth_patch')]:
    run(['dotnet','build',C/(project+'.csproj'),'--ignore-failed-sources','-o',B/folder])
inputs=B/'cloth_inputs'
for folder in [inputs,B/'cooked_cloth']:
    assert folder.resolve().parent==B.resolve()
    if folder.exists():shutil.rmtree(folder)
inputs.mkdir()
# Each build has deterministic mesh GUIDs; no stale unrelated JSON inputs allowed.
run(['dotnet',B/'cloth_probe/NativeClothProbe.dll',B/'uncooked.tpac','wdr_canglan_body','--dump-segments',inputs])
expected={g['name'] for g in json.loads((B/'geometry.json').read_text()) if g['cloth']}
assert {json.loads(p.read_text())['name'] for p in inputs.glob('*.mesh.json')}==expected
policy={'default':{'unanchored':'error'},'meshes':{name+'.lod1':{'unanchored':'pin_upper','axis':2,'band_m':.012,'min_vertices':2,'reason':'LOD1 hair reduction can remove the thin root strip; restore the surviving upper attachment edge'} for name,kind in cfg['cloth_parts'].items() if kind=='hair'}}
(R/'tools/cloth_policy.json').write_text(json.dumps(policy,indent=2)+'\n')
run([sys.executable,C/'cook_cloth.py',inputs,B/'cooked_cloth','--policy',R/'tools/cloth_policy.json'])
run(['dotnet',B/'cloth_patch/ClothPatch.dll',B/'uncooked.tpac',B/'cooked_cloth/manifest.json',R/'module/WuduRaceTest/AssetPackages/wdr.tpac','--allow-metameshes','wdr_canglan_body'])
# Capsules are authored in bind-world coordinates and attached by native bone name.
caps=[('torso_low',[0,0,.76],[0,0,.98],.065,'pelvis','spine1'),
      ('torso_high',[0,0,.98],[0,0,1.09],.065,'spine1','spine2'),
      ('neck',[0,0,1.10],[0,0,1.16],.031,'spine2','neck'),
      ('head',[0,-.005,1.19],[0,-.005,1.27],.052,'head','head')]
for side,sign in [('l',-1),('r',1)]:
    wrist=np.array(cfg['hand_rig']['wrist_cm'])/100;wrist[0]*=sign
    caps.extend([(side+'_thigh',[sign*.075,0,.72],[sign*.09,0,.43],.055,side+'_thigh',side+'_thigh'),
                 (side+'_calf',[sign*.09,0,.40],[sign*.10,-.01,.11],.042,side+'_calf',side+'_calf'),
                 (side+'_upperarm',[sign*.14,0,1.055],[sign*.265,0,.94],.010,side+'_upperarm_twist',side+'_foretwist'),
                 (side+'_forearm',[sign*.28,0,.92],wrist.tolist(),.0095,side+'_foretwist',side+'_hand')])
root=ET.Element('bodies');body=ET.SubElement(root,'body',name='wdr_canglan_collision',owner_skeleton='wdr_skeleton');container=ET.SubElement(body,'capsules');report=[]
for name,a,b,radius,ba,bb in caps:
    a=np.array(a)*K;b=np.array(b)*K;u=b-a;length=np.linalg.norm(u);u/=length
    v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);t=np.cross(v,u)
    frame=np.eye(4);frame[:3,:3]=[u,t,v];frame[3,:3]=a
    cap=ET.SubElement(container,'capsule',name='wdr_'+name,length=f'{length:.6f}',origin='0, 0, 0',frame=', '.join(f'{x:.6f}' for x in frame.ravel()))
    points=ET.SubElement(cap,'points')
    for bone in [ba,bb]:
        point=ET.SubElement(points,'point',radius=f'{radius*K:.6f}');bones=ET.SubElement(point,'bones');ET.SubElement(bones,'bone',name=bone,weight='1.0')
    report.append(dict(name=name,endpoints_m=[a.tolist(),b.tolist()],radius_m=radius*K,bones=[ba,bb]))
ET.indent(root,space='  ');ET.ElementTree(root).write(R/'module/WuduRaceTest/ModuleData/cloth_bodies.xml',encoding='utf-8',xml_declaration=True)
(R/'reports/cloth_collision.json').write_text(json.dumps(dict(capsules=report,engine_verified=False),indent=2))
print('RACE_CLOTH_READY',len(expected),'own cooked meshes;',len(caps),'collision capsules')
