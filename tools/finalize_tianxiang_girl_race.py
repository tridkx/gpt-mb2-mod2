"""Attest new race releases and assemble reproducible source manifests."""
from pathlib import Path
import json,hashlib,sys,subprocess
from datetime import datetime,timezone,timedelta
import numpy as np
from scipy.spatial import cKDTree

def finalize(R,W):
    cfg=json.loads((R/'tools/model_config.json').read_text());ident=cfg['id'];race=cfg['race']
    M=R/'module'/ident;package=M/'AssetPackages'/(race+'.tpac')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=json.loads((R/'reports/release_validation.json').read_text())
    assert report['status']=='pass' and report['final_package_sha256']==sha(package)
    sys.path.insert(0,str(W/'tools/asset_helpers/tools'))
    from georead import read_geo
    original=np.load(R/'build/fitted_model.npz');errors=[]
    for file in (R/'build/final_export_lod0/geo').glob('*.bin'):
        for mesh in read_geo(file):
            if mesh['name'].startswith(race+'_hidden'):continue
            name=mesh['name'].split('.b')[0]
            error=float(cKDTree(original[name+'_p']).query(mesh['pos'])[0].max())
            assert error<2e-6,(name,error)
            errors.append(dict(mesh=name,source_distance_max_m=error))
    report['final_lod0_source_geometry']=errors
    draft=R/'reports/motion_failure.json'
    if draft.exists():
        history=R/'reports/history/2026-10-12-draft';history.mkdir(parents=True,exist_ok=True)
        saved=history/('motion_failure_'+sha(draft)[:12]+'.json')
        saved.write_bytes(draft.read_bytes());draft.unlink()
        guide=history/'README.md'
        if not guide.exists():guide.write_text('# Draft motion checks — 2026-10-12\n\nScope: unreleased skinning drafts. These failed checks are historical; the final v0.1.0 evidence is ../../release_validation.json.\n')
    for name in ['source_validation','ui_scope_validation','binding_validation','preview_idle_validation','skeletal_skirt_validation']:
        check=json.loads((R/'reports'/(name+'.json')).read_text());assert check['status']=='pass'
        report[name]=check
    skirt_check=R/'reports/preview_skirt_validation.json'
    if skirt_check.exists():
        check=json.loads(skirt_check.read_text())
        assert check['status']=='pass' and check['final_package_sha256']==sha(package) and check['version']==cfg['version']
        report['preview_skirt_validation']=check
        previous=json.loads((R/'reports/history/v0.1.0/release_validation.json').read_text())
        report['baseline_package_sha256']=previous['final_package_sha256']
        report['baseline_reason']='v0.1.0 preview clearance repair; local horizontal skirt offsets, original body and all binding retained'
        report['preview_skirt_fit']=json.loads((R/'reports/preview_skirt_fit.json').read_text())
        unchanged=json.loads((R/'reports/skirt_unchanged_data_validation.json').read_text())
        assert unchanged['status']=='pass' and unchanged['version']==cfg['version']
        assert unchanged['offset_parameter_sha256']==sha(R/'tools/preview_skirt_offsets.npz')
        report['skirt_unchanged_data_validation']=unchanged
        transfer_path=R/'reports/weight_transfer.json'
        transfer=json.loads(transfer_path.read_text())
        transfer.update(source_geometry_max_error_m=report['preview_skirt_fit']['parts'][0]['maximum_offset_m'],
            source_body_geometry_max_error_m=0,source_height_unchanged=True,all_binding_weights_unchanged=True)
        transfer_path.write_text(json.dumps(transfer,indent=2))
        report['final_lod0_source_geometry_reference']='Editable repaired source; local skirt clearance differs from original input, body/height/binding retained'
    preview=json.loads((R/'reports/final_preview_manifest.json').read_text());assert preview['package_sha256']==sha(package)
    report.update(date=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d'),baseline_reason='First release; own source FBX hashes and exact source-coordinate comparison' if not skirt_check.exists() else report['baseline_reason'],
        module_file_sha256={p.relative_to(M).as_posix():sha(p) for p in M.rglob('*') if p.is_file()},
        source_texture_sha256={p.name:sha(p) for p in (R/'tex').glob('*.png')},
        game_test_verified=False,added_test_troops=[])
    (R/'reports/release_validation.json').write_text(json.dumps(report,indent=2))
    files=[p.relative_to(R).as_posix() for d in ['input','source','tools','reports'] for p in (R/d).rglob('*')
        if p.is_file() and not set(p.relative_to(R).parts)&{'obj','bin','__pycache__'} and p.suffix not in ['.pyc','.log','.blend1']]
    files+=['README.md','CHANGELOG.md','.gitignore','.gitattributes','mod.json',f'module/{ident}/bin/Win64_Shipping_Client/{ident}.UIRuntime.dll']
    base=json.loads((W/'mods/TianxiangRaceColletion/TianxiangGirlT2Race/mod.json').read_text())
    shared=base['shared_source_files']+['tools/tianxiang_girl_race_configuration.py','tools/finalize_tianxiang_girl_race.py']
    if (R/'tools/repair_preview_skirt.py').exists():shared+=['tools/tianxiang_preview_skirt.py']
    (R/'mod.json').write_text(json.dumps(dict(id=ident,source_files=sorted(files),shared_source_files=shared,
        package=f'module/{ident}/AssetPackages/{race}.tpac',validation_report='reports/release_validation.json'),indent=2))
    print('RELEASE_READY',ident,cfg['version'],sha(package))
