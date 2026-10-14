"""Build an isolated coherent skirt candidate; do not install implicitly."""
from pathlib import Path
import sys,json
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(workspace_root(R)/'tools/cloth_compiler'))
import build_mapped
from prepare_outer_driver import prepare
from coherent_layer_mapping import mapper

if __name__=='__main__':
    path=R/'tools/model_config.json';original=path.read_bytes();cfg=json.loads(original)
    cfg['mapped_cloth']=json.loads((R/'tools/outer_driver_config.json').read_text())
    try:
        path.write_text(json.dumps(cfg,indent=2)+'\n')
        code=Path(build_mapped.__file__).read_text()
        # Reduced LOD vertices close to front attachments can be nearest to
        # a decorative source island. Classify the actual front skirt region
        # geometrically; the back/head ornament remains on its own island.
        code=code.replace('        mi=np.zeros(',
            "        if name=='yqs_part_10':\n"
            "            mask|=(positions[:,1]>.10)&(positions[:,2]>.65)&(positions[:,2]<1.13)\n"
            '        mi=np.zeros(')
        namespace={'__name__':'outer_driver_builder','__file__':build_mapped.__file__}
        exec(compile(code,build_mapped.__file__,'exec'),namespace)
        namespace['prepare']=prepare;namespace['project']=mapper(R)
        namespace['build'](R)
    finally:
        path.write_bytes(original)
