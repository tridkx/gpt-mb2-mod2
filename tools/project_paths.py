"""Resolve flat projects and the user's grouped Tianxiang collection."""
from pathlib import Path
def resolve_project(workspace,name):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
        raise ValueError('Invalid project ID')
    workspace=Path(workspace).resolve()
    candidates=[workspace/'mods'/name,workspace/'mods/TianxiangCollection/sets'/name]
    matches=[p for p in candidates if (p/'mod.json').is_file()]
    if len(matches)!=1:raise ValueError(f'Expected one configured project for {name}, found {len(matches)}')
    return matches[0]
