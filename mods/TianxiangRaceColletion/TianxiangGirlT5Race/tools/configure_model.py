from pathlib import Path
import sys
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(workspace_root(R)/'tools'))
from tianxiang_girl_race_configuration import configure
configure(R)

import json
p=R/'tools/model_config.json';cfg=json.loads(p.read_text());cfg['version']='v0.1.1'
p.write_text(json.dumps(cfg,indent=2))

parts=sorted(json.loads((R/'input/parts.json').read_text()),key=lambda x:x['name'])
cfg['minimum_part_ratios']={cfg['race']+'_part_'+str([p['name'] for p in parts].index(source)).zfill(2):1.0 for source in cfg['legs_sources']}
p.write_text(json.dumps(cfg,indent=2))
