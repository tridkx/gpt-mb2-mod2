from pathlib import Path
import sys
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(workspace_root(R)/'tools'))
from tianxiang_girl_race_configuration import configure
configure(R)
