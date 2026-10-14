"""Build an isolated simplified-skirt candidate using the shared native mapper."""
from pathlib import Path
import sys
import json
import subprocess
from workspace_paths import workspace_root

ROOT = Path(__file__).resolve().parents[1]
COMMON = workspace_root(ROOT) / 'tools/cloth_compiler'
sys.path.insert(0, str(COMMON))
import build_mapped
from prepare_skirt_proxy import prepare

if __name__ == '__main__':
    subprocess.run(['D:/Blender Foundation/Blender 5.2/blender.exe', '--background',
                    '--factory-startup', '--python-exit-code', '1', '--python',
                    str(ROOT/'tools/simplify_primary_skirt.py')], check=True)
    # The shared mapper reads model_config; keep the released configuration
    # byte-identical after the isolated build, including on build failure.
    path = ROOT/'tools/model_config.json'
    original = path.read_bytes()
    cfg = json.loads(original)
    cfg['mapped_cloth'] = json.loads((ROOT/'tools/skirt_proxy_config.json').read_text())
    try:
        path.write_text(json.dumps(cfg, indent=2)+'\n')
        build_mapped.prepare = prepare
        build_mapped.build(ROOT)
    finally:
        path.write_bytes(original)
