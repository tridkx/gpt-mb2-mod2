"""Locate shared tools in the workspace or this mod's portable source archive."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
shared=ROOT/'workspace_tools/cloth_compiler'
if not (shared/'__init__.py').is_file():
    for parent in ROOT.parents:
        shared=parent/'tools/cloth_compiler'
        if (shared/'__init__.py').is_file():break
    else:raise FileNotFoundError('Shared tools/cloth_compiler missing')
sys.path.insert(0,str(shared.parent))
SHARED=shared
