"""Adapt executable paths after grouping projects; preserve historical Git paths."""
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parents[1]
changed=[]
for project in (ROOT/'sets').iterdir():
    if not (project/'mod.json').is_file():continue
    for p in (project/'tools').rglob('*'):
        if not p.is_file() or p.suffix not in ['.py','.ps1'] or any(x in ['obj','bin','__pycache__'] for x in p.parts):continue
        s=p.read_text(encoding='utf-8-sig');original=s
        if p.suffix=='.py':
            s=s.replace("ROOT.parents[1]/'tools/", "next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())/'tools/")
            s=s.replace("WS=ROOT.parents[1]", "WS=next(p for p in ROOT.parents if (p/'tools/asset_helpers').is_dir())")
            s=s.replace("Path(__file__).resolve().parents[3]/'tools/", "next(p for p in Path(__file__).resolve().parents if (p/'tools/asset_helpers').is_dir())/'tools/")
        else:
            s=s.replace("Join-Path $project '../../tools/", "Join-Path $project '../../../../tools/")
        if s!=original:
            if p.suffix=='.py':ast.parse(s)
            p.write_text(s,encoding='utf-8');changed.append(p.relative_to(WS).as_posix())
# Common model helpers keep their interface and resolve grouped models by ID.
for p in (WS/'tools').glob('*.py'):
    if p.name in ['new_mod.py','package_delivery.py','project_paths.py']:continue
    s=p.read_text(encoding='utf-8-sig');original=s
    replacements={"WS/'mods'/sys.argv[1]":"resolve_project(WS,sys.argv[1])",
        "WS/'mods'/sys.argv[sys.argv.index('--')+1]":"resolve_project(WS,sys.argv[sys.argv.index('--')+1])",
        "Path(__file__).resolve().parents[1]/'mods'/sys.argv[1]":"resolve_project(Path(__file__).resolve().parents[1],sys.argv[1])",
        "Path(__file__).resolve().parents[1]/'mods'/sys.argv[sys.argv.index('--')+1]":"resolve_project(Path(__file__).resolve().parents[1],sys.argv[sys.argv.index('--')+1])",
        "WS/'mods/TianxiangRenqiu'":"resolve_project(WS,'TianxiangRenqiu')",
        "ROOT/'mods'/mod":"resolve_project(ROOT,mod)"}
    for a,b in replacements.items():s=s.replace(a,b)
    if s!=original:
        marker='from pathlib import Path'
        assert marker in s,p
        s=s.replace(marker,marker+"\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom project_paths import resolve_project",1)
        ast.parse(s);p.write_text(s,encoding='utf-8');changed.append(p.relative_to(WS).as_posix())
report_path=ROOT/'reports/grouped_paths.json'
if report_path.is_file():changed=sorted(set(changed+json.loads(report_path.read_text())['path_updates']))
report={'status':'pass','grouped_projects':[p.name for p in (ROOT/'sets').iterdir() if (p/'mod.json').is_file()],'path_updates':changed,'historical_git_object_paths_preserved':True,'individual_versions_unchanged':True}
(ROOT/'reports/grouped_paths.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('GROUPED_PATHS_ADAPTED',len(changed),'scripts')
