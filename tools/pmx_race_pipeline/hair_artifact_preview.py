"""Render final geometry including cloth drivers to expose accidental proxy drawing."""
import sys
from pathlib import Path
import shutil
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import SERIES,config
arguments=sys.argv[sys.argv.index('--')+1:];label=arguments[0]
if arguments[1:]==['all']:arguments=[label]+[p.name for p in SERIES.iterdir() if (p/'reports/hair_proxy_visibility_fix.json').exists()]
for identity in arguments[1:]:
    root=SERIES/identity;c=config(root)
    code=(Path(__file__).parent/'templates/render_final.py.tpl').read_text(encoding='utf8')
    code=code.replace("if m['name'].startswith('emilie_part_')", "if m['name'].startswith('emilie_part_') or m['name']=='emilie_cloth_proxy'")
    code=code.replace("ROOT/'reports'/('final_'+", "ROOT/'build/hair_artifact'/('"+label+"_'+")
    for old,new in [('EmilieRace',c['id']),('emilie',c['prefix'])]:code=code.replace(old,new)
    (root/'build/hair_artifact').mkdir(exist_ok=True)
    sys.argv=[sys.argv[0],'--','0','--rest']
    try:exec(compile(code,'hair_artifact_render','exec'),{'__name__':'__main__','__file__':str(root/'tools/render_hair_artifact.py')})
    except SystemExit as error:
        if error.code not in [None,0]:raise
    for path in (root/'build/hair_artifact').glob(label+'_*.png'):shutil.copy2(path,root/'reports'/('hair_proxy_'+path.name))
