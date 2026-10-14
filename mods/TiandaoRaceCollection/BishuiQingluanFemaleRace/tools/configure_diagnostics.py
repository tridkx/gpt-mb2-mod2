"""Derive source animation rates from the installed Native clip durations."""
import json,re,sys,subprocess
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);sys.path.insert(0,str(W/'tools/asset_helpers/previewer'))
from baker.animation import parse_animjson
cfg=json.loads((R/'mod.json').read_text());motions=[];clips=[]
for name,clip in [('ui_neutral_female','anim_female_custom'),('run','run_forward_unarmed'),('riding','rider_gallop_bow')]:
 raw=json.loads((R/'reports'/(name+'.json')).read_text());a=parse_animjson(raw);output=subprocess.check_output(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','clip','D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/AssetPackages/animation_clips.tpac',clip],text=True,encoding='utf-8');match=re.search(r'duration=([\d.]+) animation=([^\s]+)',output);assert match and match[2]==raw['guid'];duration=float(match[1]);fps=a['tEnd']/duration
 motion=dict(name=name,path='reports/'+name+'.json',fps=fps)
 if name=='ui_neutral_female':motion['end']=122
 motions.append(motion);clips.append(dict(label=name,clip=clip,source_t_end=a['tEnd'],duration_seconds=duration,fps=fps,metadata=output))
common=dict(skeleton='reports/final_skeleton.json',capsules='module/BishuiQingluanFemaleRace/ModuleData/cloth_bodies.xml',body='bql_collision',motions=motions,settings=dict(warmup=30,substeps=2,iterations=5))
cfg['cloth_diagnostics']=dict(enabled=True,mode='report',probe='build/cloth_probe/NativeClothProbe.dll',targets=[dict(metamesh='bql_body',lods=[0,1],**common),dict(metamesh='bql_cloth_proxy',lods=[0],**common)])
(R/'reports/animation_rates.json').write_text(json.dumps(clips,indent=2));(R/'mod.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('DIAGNOSTICS_CONFIGURED',[(m['name'],m['fps']) for m in motions])
