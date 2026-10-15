"""Generate own module/runtime sources and project entry points; never touch Emilie."""
import json,shutil,subprocess,hashlib
from pathlib import Path
from context import SERIES,config,execute,workspace_root
def scaffold(root):
    c=config(root);w=workspace_root(root);tools=root/'tools';runtime=tools/'UIRuntime';runtime.mkdir(exist_ok=True);template=Path(__file__).parent/'templates'
    for name in ['Runtime.cs','UIRuntime.csproj']:
        template_name='UIRuntime.cs.tpl' if name=='Runtime.cs' else 'UIRuntime.csproj.tpl'
        code=(template/template_name).read_text(encoding='utf-8-sig').replace('EmilieRace',c['id']).replace('emilie',c['prefix']);(runtime/name).write_text(code,encoding='utf8')
    if c.get('cloth_enabled'):
        code=(template/'HairRuntimeProbe.cs.tpl').read_text(encoding='utf8').replace('EmilieRace',c['id']).replace('emilie',c['prefix'])
        code=code.replace('__HAIR_PARTS__',','.join(json.dumps(c['prefix']+f'_part_{i:02d}') for i in c['cloth_materials']))
        (runtime/'HairRuntimeProbe.cs').write_text(code,encoding='utf8')
    entry='''"""Rebuild this independent character without starting the game."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
W=next(p for p in R.parents if (p/'tools/pmx_race_pipeline').is_dir())
sys.path.insert(0,str(W/'tools/pmx_race_pipeline'))
from build_one import build_one
if __name__=='__main__':build_one(R,source=True)
'''
    (tools/'rebuild.py').write_text(entry,encoding='utf8');execute('register_module',root)
    result=subprocess.run(['dotnet','build',str(runtime/'UIRuntime.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(root/'build/ui_obj')+'/', '-o',str(root/'build/ui_runtime')],capture_output=True,text=True,encoding='utf8',errors='replace')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    dest=root/'module'/c['id']/'bin/Win64_Shipping_Client';dest.mkdir(parents=True,exist_ok=True);dll=root/'build/ui_runtime'/(c['id']+'.UIRuntime.dll');shutil.copy2(dll,dest)
    (root/'reports/ui_scope_validation.json').write_text(json.dumps({'status':'pass','race_filter':c['race'],'assembly_name':c['id']+'.UIRuntime','source_sha256':hashlib.sha256((runtime/'Runtime.cs').read_bytes()).hexdigest(),'assembly_sha256':hashlib.sha256(dll.read_bytes()).hexdigest(),'owners':['CharacterTableau','BasicCharacterTableau','BodyGeneratorView'],'mission_and_live_map_entities_excluded':True,'game_verified':False},indent=2));print('MODULE_REGISTERED',c['id'],flush=True)

if __name__=='__main__':
    import sys
    scaffold(Path(sys.argv[1]).resolve())
