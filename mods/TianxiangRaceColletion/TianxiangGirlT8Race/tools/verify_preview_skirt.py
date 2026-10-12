from pathlib import Path
import sys,runpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1]
sys.argv=['tianxiang_preview_skirt.py','verify',str(R)]
runpy.run_path(str(workspace_root(R)/'tools/tianxiang_preview_skirt.py'),run_name='__main__')
