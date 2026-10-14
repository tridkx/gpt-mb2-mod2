"""Build an explicit project's source without a collection inventory dependency."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import execute
from source_preview import preview
root=Path(sys.argv[sys.argv.index('--')+1]).resolve()
for stage in ['create_source','export_geometry','verify_source']:execute(stage,root)
preview(root)
