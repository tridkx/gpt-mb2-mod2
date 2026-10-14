"""Prove only sleeve skinning changed; skirt/proxy/cooked data remain identical."""
import sys,json,subprocess,hashlib
from pathlib import Path
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R);B=R/'build';sys.path.insert(0,str(W/'tools/cloth_compiler'))
from verify_mapped import streams
cfg=json.loads((R/'tools/model_config.json').read_text());old=B/'sleeve_skin_baseline_v0.1.1.tpac';new=R/'module'/cfg['id']/'AssetPackages/bql.tpac';mb='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe';rows=[]
def run(args):subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)
for lod in range(4):
 a=B/f'skin_before_lod{lod}';b=B/f'skin_after_lod{lod}';run([mb,'exportmod',old,a,lod]);run([mb,'exportmod',new,b,lod]);before={};after={}
 for p in (a/'geo').glob('*.bin'):before.update(streams(p))
 for p in (b/'geo').glob('*.bin'):after.update(streams(p))
 assert before.keys()==after.keys()
 changed=[]
 for name,x in before.items():
  z=after[name]
  if not name.startswith('bql_part_13'):assert x==z,('non-sleeve changed',name);continue
  assert {k:v for k,v in x.items() if k!='fields'}=={k:v for k,v in z.items() if k!='fields'}
  for field,data in x['fields'].items():
   if data!=z['fields'][field]:assert field in ['bones','weights'];changed.append(field)
 rows.append(dict(lod=lod,changed_sleeve_fields=sorted(set(changed)),all_non_sleeve_gpu_streams_identical=True))
for label,pkg in [('before',old),('after',new)]:run(['dotnet',B/'mapped_patch/MappedClothPatch.dll','--inspect',pkg,'bql_body','bql_cloth_proxy',B/f'skin_{label}_data'])
def segment_hashes(label):
 result={}
 for m in json.loads((B/f'skin_{label}_data/inspection.json').read_text()):
  for s in m['segments']:result[(m['Name'],s['OwnerGuid'],s['TypeGuid'])]=s['sha256']
 return result
assert segment_hashes('before')==segment_hashes('after')
report=dict(status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),lods=rows,all_cloth_and_mapping_segments_identical=True,skirt_and_other_resources_preserved=True,game_verified=False)
(R/'reports/sleeve_patch_validation.json').write_text(json.dumps(report,indent=2));print('SLEEVE_PATCH_VERIFIED: only bone indices/weights changed, skirt and cloth bytes preserved')
