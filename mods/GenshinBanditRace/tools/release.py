"""Locate the workspace release helper, or use the copy supplied in a source archive."""
from pathlib import Path
import runpy
import sys

root=Path(__file__).resolve().parents[1]
candidates=[parent/'tools/bandit_mod_release.py' for parent in root.parents]
candidates.append(root/'workspace_tools/bandit_mod_release.py')
helper=next((p for p in candidates if p.is_file()),None)
if helper is None: raise FileNotFoundError('bandit_mod_release.py is missing')
sys.argv[1:1]=['--mod','GenshinBanditRace','--project-root',str(root)]
runpy.run_path(str(helper),run_name='__main__')
