"""Reuse CPU trajectories only after exact equality of all simulation inputs."""
import json,sys,hashlib,copy
from context import SERIES,workspace_root
from finalize import finalize
w=workspace_root(SERIES);sys.path.insert(0,str(w/'tools'))
from cloth_simulator.pipeline import normalize,fingerprint,valid_cached,sha,write_summary
for path in SERIES.glob('*/reports/hair_proxy_visibility_fix.json'):
    root=path.parent.parent;proof=json.loads(path.read_text());assert proof['status']=='pass'
    assert all(proof[key] for key in ['all_lod_body_geometry_bytes_unchanged','proxy_stream_bytes_unchanged','cloth_payloads_mappings_and_settings_unchanged','skeleton_bytes_unchanged','original_encoded_textures_unchanged'])
    finalize(root);cfg=json.loads((root/'mod.json').read_text(encoding='utf8'));old=json.loads((root/'reports/cloth_diagnostics.json').read_text())
    assert old['package_sha256']==proof['baseline_package_sha256'] and old['status']!='error'
    spec,package,probe,inputs=normalize(root,cfg);stamp,inventory=fingerprint(root,spec,inputs)
    assert spec==old['config']
    exceptions={'mod/mod.json','mod/'+cfg['package']}
    assert inventory.keys()==old['inputs'].keys()
    assert all(value==old['inputs'][key] for key,value in inventory.items() if key not in exceptions),'Nonmaterial simulation input changed'
    assert sha(package)==proof['final_package_sha256']
    new=copy.deepcopy(old);new.update(fingerprint=stamp,inputs=inventory,package_sha256=sha(package),simulation_rerun=False,material_only_equivalence={'proof':'reports/hair_proxy_visibility_fix.json','proof_sha256':sha(path),'baseline_package_sha256':proof['baseline_package_sha256'],'basis':'All LOD and proxy streams, cloth settings, payloads and mappings unchanged; collision, skeleton, motion and solver input hashes identical. Original trajectory provenance retained.'})
    assert valid_cached(root,new,stamp)
    original=root/'build/hair_proxy_fix/v0.1.0/cloth_diagnostics.json'
    if not original.exists():original.write_text(json.dumps(old,indent=2))
    write_summary(root/'reports/cloth_diagnostics.json',new);print('SIMULATION_INPUT_EQUIVALENCE',root.name,flush=True)
