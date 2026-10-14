"""Common context; every model keeps its own configuration and output root."""
from pathlib import Path
import json,sys
W=Path(__file__).resolve().parents[2]
SERIES=W/'mods/GenshinRaceCollection'

def config(root):return json.loads((Path(root)/'tools/model_config.json').read_text(encoding='utf8'))

def workspace_root(project):
    for p in Path(project).resolve().parents:
        if (p/'tools/asset_helpers').is_dir():return p
    raise RuntimeError('Restore workspace_tools to workspace tools/ before rebuilding')

def execute(stage,root):
    root=Path(root).resolve();c=config(root);path=Path(__file__).parent/'templates'/(stage+'.py.tpl');code=path.read_text(encoding='utf-8-sig')
    code=code.replace('EmilieRace',c['id']).replace('emilie',c['prefix']).replace('Emilie Race',c['module_name']).replace('Emilie',c['display_name'])
    code=code.replace("'input/original/艾梅莉埃.pmx'",repr(c['source_model']))
    code=code.replace('艾梅莉埃',c['display_name'])
    code=code.replace("read_text()","read_text(encoding='utf8')")
    sys.path.insert(0,str(Path(__file__).parent))
    namespace={'__name__':'__main__','__file__':str(root/'tools'/(stage+'.py')),'PROJECT_ROOT':root}
    try:exec(compile(code,str(path),'exec'),namespace)
    except SystemExit as error:
        if error.code not in (None,0):raise

if __name__=='__main__':execute(sys.argv[1],sys.argv[2])
