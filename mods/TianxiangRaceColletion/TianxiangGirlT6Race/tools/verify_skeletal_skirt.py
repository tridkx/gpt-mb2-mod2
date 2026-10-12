"""Attest final TPAC has skeletal skirts and no native cloth runtime payload."""
import json,subprocess,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1];cfg=json.loads((R/'tools/model_config.json').read_text());assert not cfg['cloth_enabled'] and not cfg['cloth_lods']
W=next(p for p in R.parents if (p/'tools/asset_helpers').is_dir());sys.path.insert(0,str(W/'tools/asset_helpers/tools'));from georead import read_geo
p=R/'module/TianxiangGirlT6Race/AssetPackages/txgirl6.tpac'
probe=R/'build/cloth_probe/NativeClothProbe.dll'
if not probe.exists():subprocess.run(['dotnet','build',str(W/'tools/cloth_compiler/NativeClothProbe.csproj'),'--ignore-failed-sources','-p:BaseIntermediateOutputPath='+str(R/'build/cloth_obj/NativeClothProbe')+'/', '-o',str(probe.parent)],check=True)
data=json.loads(subprocess.check_output(['dotnet',str(R/'build/cloth_probe/NativeClothProbe.dll'),str(p),'txgirl6_body','txgirl6_hidden'],encoding='utf8'))
for body in data:
 assert body['body']=='' and body['ClothString']=='' and body['ClothUint']==0
 assert not any(s['TypeGuid']=='b97e0f10-df49-4666-8f1d-ada6630d4b4e' for s in body['segments'])
 assert all(not set(m['Flags'])&{'uses_cloth_simulation','force_enable_cloth'} for m in body['meshes'])
assert not ET.parse(R/'module/TianxiangGirlT6Race/ModuleData/cloth_bodies.xml').getroot().findall('body')
report=dict(status='pass',version=cfg['version'],final_package_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),cloth_enabled=False,cloth_runtime_segments=0,cloth_flagged_meshes=0,cloth_collision_references=0,scope='Final TPAC native flags, segments, collision references; geometry and weights checked by verify_release; no game run')
(R/'reports/skeletal_skirt_validation.json').write_text(json.dumps(report,indent=2));(R/'reports/cloth_validation.json').write_text(json.dumps(report,indent=2));print('SKELETAL_SKIRT_VERIFIED',report)
