"""Freshly extract native drivers, then reuse only identical numerical inputs."""
import json,sys,copy,subprocess
from pathlib import Path
from context import SERIES,workspace_root
from finalize import finalize
w=workspace_root(SERIES);sys.path.insert(0,str(w/'tools'))
from cloth_simulator.pipeline import normalize,fingerprint,valid_cached,sha,write_summary
for path in SERIES.glob('*/reports/runtime_resource_fix.json'):
    root=path.parent.parent;fix=json.loads(path.read_text());finalize(root)
    if not fix['native_driver_role']:continue
    cfg=json.loads((root/'mod.json').read_text(encoding='utf8'));old=json.loads((root/'build/runtime_resource_fix/v0.1.1/cloth_diagnostics.json').read_text())
    assert old['package_sha256']==fix['baseline_package_sha256'] and old['status']!='error'
    spec,package,probe,inputs=normalize(root,cfg);assert spec==old['config'];stamp,inventory=fingerprint(root,spec,inputs)
    excluded={'mod/mod.json','mod/'+cfg['package']}
    excluded.update(k for k in inventory if k.startswith('mod/build/cloth_probe/NativeClothProbe.'))
    assert inventory.keys()==old['inputs'].keys()
    assert all(v==old['inputs'][k] for k,v in inventory.items() if k not in excluded),'Skeleton, collider, animation or solver input changed'
    target=next(i for i,t in enumerate(spec['targets']) if t['metamesh'].endswith('_cloth_proxy'));previous=root/old['run_directory']/f'target_{target:02d}/input';current=root/'build/runtime_resource_fix/current_driver';current.mkdir(exist_ok=True)
    proc=subprocess.run(['dotnet',str(probe),str(package),spec['targets'][target]['metamesh'],'--dump-segments',str(current)],check=True,capture_output=True,text=True)
    metadata=json.loads(proc.stdout)[0];driver=metadata['meshes'][0];assert metadata['body']=='' and driver['Flags']==[]
    files=[p for p in current.iterdir() if p.is_file()];assert any(p.name.endswith('.mesh.json') for p in files)
    assert all(p.read_bytes()==(previous/p.name).read_bytes() for p in files),'Extracted numerical cloth inputs changed'
    proof={'status':'pass','version':'v0.1.2','package_sha256':sha(package),'current_extraction':str(current.relative_to(root)),'files':{p.name:sha(p) for p in files},'original_trajectory_provenance_retained':True,'native_engine_behavior_verified':False}
    (root/'reports/native_driver_input_validation.json').write_text(json.dumps(proof,indent=2))
    # Account for the added proof in the source manifest before calculating cache identity.
    finalize(root);cfg=json.loads((root/'mod.json').read_text(encoding='utf8'));spec,package,probe,inputs=normalize(root,cfg);stamp,inventory=fingerprint(root,spec,inputs)
    report=copy.deepcopy(old);report.update(fingerprint=stamp,inputs=inventory,package_sha256=sha(package),simulation_rerun=False,numerical_input_reuse={'proof':'reports/native_driver_input_validation.json','proof_sha256':sha(root/'reports/native_driver_input_validation.json'),'basis':'Fresh flagless-driver extraction is byte-identical to prior solver mesh, edit data and payload; skeleton, collision, animation and solver inputs unchanged. Engine driver registration is outside CPU solver coverage.','native_engine_behavior_verified':False})
    assert valid_cached(root,report,stamp);write_summary(root/'reports/cloth_diagnostics.json',report);print('FRESH_DRIVER_INPUT_VERIFIED',root.name,flush=True)
