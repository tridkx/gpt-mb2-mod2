from pathlib import Path
import sys
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path.insert(0,str(W/'tools'))
from finalize_tianxiang_girl_race import finalize
finalize(R,W)
