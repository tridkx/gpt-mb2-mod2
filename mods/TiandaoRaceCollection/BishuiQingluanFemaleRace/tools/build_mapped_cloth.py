"""Use the shared native compiler with this source's explicit skirt selection."""
from pathlib import Path
import sys,json,shutil
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)
sys.path.insert(0,str(W/'tools/cloth_compiler'))
import build_mapped
from prepare_proxy import prepare
from coherent_layer_mapping import mapper
from cloth_regions import skirt_mask
code=Path(build_mapped.__file__).read_text()
old="skirt_lookup[name]=(cKDTree(positions),np.isin(labels[owner],selected),labels[owner])"
assert old in code
code=code.replace(old,"skirt_lookup[name]=(cKDTree(positions),source[name+'_sk'],labels[owner])")
code=code.replace("        mi=np.zeros(","        if name in skirt_lookup:mask=skirt_mask(name,positions,np.array(render['indices']).reshape(-1,3),source)\n        mi=np.zeros(")
namespace={'__name__':'bql_mapped_builder','__file__':build_mapped.__file__};exec(compile(code,build_mapped.__file__,'exec'),namespace);namespace['prepare']=prepare;namespace['project']=mapper(R)
namespace['skirt_mask']=skirt_mask
namespace['build'](R)
import verify_mapped
verify_mapped.verify(R)
cfg=json.loads((R/'tools/model_config.json').read_text());shutil.copy2(R/'build/mapped_candidate.tpac',R/'module'/cfg['id']/'AssetPackages/bql.tpac')
