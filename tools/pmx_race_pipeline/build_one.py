"""Build independent resources and offline checks for one explicitly selected model."""
from pathlib import Path
import json,subprocess,sys,shutil
from context import config,execute,workspace_root
from scaffold import scaffold
from collisions import write_collisions
from cloth import build_cloth

def build_one(root,source=False):
    root=Path(root).resolve();c=config(root);w=workspace_root(root);print('BUILD_BEGIN',c['id'],flush=True)
    if source:
        from prepare import prepare
        from references import prepare_references
        prepare(root);prepare_references(root)
        subprocess.run(['D:/Blender Foundation/Blender 5.2/blender.exe','--background','--factory-startup','--python-exit-code','1','--python',str(w/'tools/pmx_race_pipeline/source_one.py'),'--',str(root)],check=True)
    scaffold(root);execute('build_package',root)
    if c['cloth_enabled']:write_collisions(root);build_cloth(root)
    execute('verify_release',root);print('BUILD_OFFLINE_COMPLETE',c['id'],flush=True)

if __name__=='__main__':build_one(Path(sys.argv[1]),source='--source' in sys.argv)
