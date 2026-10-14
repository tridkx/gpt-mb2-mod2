"""Rebuild this independent character without starting the game."""
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
W=next(p for p in R.parents if (p/'tools/pmx_race_pipeline').is_dir())
sys.path.insert(0,str(W/'tools/pmx_race_pipeline'))
from build_one import build_one
if __name__=='__main__':build_one(R,source=True)
