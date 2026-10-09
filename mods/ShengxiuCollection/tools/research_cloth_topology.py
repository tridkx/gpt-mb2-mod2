"""Compatibility entry point for shared native topology inspection."""
import shared_cloth
from cloth_compiler.research_cloth_topology import inspect
if __name__=='__main__':
    import sys,json
    from pathlib import Path
    print(json.dumps([inspect(Path(p)) for p in sys.argv[1:]],indent=2))
