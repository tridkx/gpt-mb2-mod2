"""Locate the shared toolchain without assuming a fixed project depth."""
from pathlib import Path

def workspace_root(project):
    for parent in Path(project).resolve().parents:
        if (parent/'tools/asset_helpers').is_dir():
            return parent
    raise RuntimeError('Restore workspace_tools to workspace tools/ before rebuilding')
