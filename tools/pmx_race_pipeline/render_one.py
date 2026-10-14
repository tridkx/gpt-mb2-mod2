import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import execute
root=Path(sys.argv[sys.argv.index('--')+1]);sys.argv=[sys.argv[0],'--','0'];execute('render_final',root)
