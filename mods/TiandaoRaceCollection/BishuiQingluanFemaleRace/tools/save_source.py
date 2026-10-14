"""Store the actual native proxy alongside the visible, unchanged source."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
path=W/'tools/cloth_compiler/save_proxy_source.py'
sys.argv=['save_source','--',str(R)]
code=path.read_text().replace('Native shared cloth proxy with layer links; rendered body remains unchanged','Native shared skirt chart plus independent sleeve/ribbon/fiber islands; visible geometry preserved')
exec(compile(code,str(path),'exec'))
