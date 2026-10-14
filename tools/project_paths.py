"""Resolve standalone projects, collection sets and grouped character series."""
from pathlib import Path
def resolve_project(workspace,name):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
        raise ValueError('Invalid project ID')
    workspace=Path(workspace).resolve()
    candidates=[workspace/'mods'/name,workspace/'mods/TianxiangCollection/sets'/name,
                workspace/'mods/ResidentEvil'/name,workspace/'mods/Xianjian7Race'/name,
                workspace/'mods/TianxiangRaceColletion'/name,
                workspace/'mods/TiandaoRaceCollection'/name]
    matches=[p for p in candidates if (p/'mod.json').is_file()]
    if len(matches)!=1:raise ValueError(f'Expected one configured project for {name}, found {len(matches)}')
    return matches[0]
