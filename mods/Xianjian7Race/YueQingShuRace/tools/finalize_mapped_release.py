"""Finalize mapped resources without converting approximate warnings to pass."""
from pathlib import Path
import json,hashlib,subprocess,sys
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)

def main():
    package=R/'module/YueQingShuRace/AssetPackages/yqs.tpac'
    sha=hashlib.sha256(package.read_bytes()).hexdigest()
    assert sha==hashlib.sha256((R/'build/mapped_candidate.tpac').read_bytes()).hexdigest()
    subprocess.run([sys.executable,'-B','-X','utf8',str(W/'tools/cloth_compiler/verify_mapped.py'),str(R)],check=True)
    structure=json.loads((R/'reports/mapped_structure_validation.json').read_text())
    assert structure['status']=='pass' and structure['candidate_sha256']==sha
    source=json.loads((R/'reports/source_validation.json').read_text());assert source['status']=='pass'
    report=json.loads((R/'reports/release_validation.json').read_text());assert report['status']=='pass' and report['final_package_sha256']==sha
    acceptance=json.loads((R/'reports/game_acceptance.json').read_text())
    matched=acceptance['package_sha256']==sha
    cfg=json.loads((R/'tools/model_config.json').read_text())
    report.update(version=cfg['version'],cloth_mode='mapped_outer_driver',cloth_enabled=True,cloth_lods=[0,1,2,3],
        check_scope='Final resource/source/visible preservation and native mapping checks; approximate dynamics kept separate',
        user_game_acceptance=dict(**acceptance,runtime_assets_unchanged=matched),
        current_cloth_game_acceptance='accepted' if matched and acceptance['accepted'] else 'pending',
        source_geometry_max_error_m=source['source_geometry_max_error_m'],source_proportions_preserved=True,
        cloth_collision_xml_sha256=hashlib.sha256((R/'module/YueQingShuRace/ModuleData/cloth_bodies.xml').read_bytes()).hexdigest(),
        approximate_cloth_diagnostics='incomplete_mapped_body_unsupported; do not interpret as a game failure')
    (R/'reports/release_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    cloth=dict(status='pass',mode='mapped_outer_driver',scope='Native structure and final render-stream preservation only',
        final_package_sha256=sha,proxy_simulation_vertices=structure['proxy_simulation_vertices'],
        mapped_render_segments=structure['render_mapping_segments'],lods=structure['lods'],
        user_game_accepted=bool(matched and acceptance['accepted']),assistant_ran_game=False,
        dynamic_diagnostic_status='needs_review',mapped_body_shared_diagnostic_status='incomplete',
        slight_penetration_user_tolerance=True)
    (R/'reports/cloth_validation.json').write_text(json.dumps(cloth,indent=2)+'\n')
    source.update(version=cfg['version'],final_package_sha256=sha,cloth_mode='mapped_outer_driver')
    (R/'reports/source_validation.json').write_text(json.dumps(source,indent=2)+'\n')
    print('MAPPED_RELEASE_FINALIZED',cfg['version'],sha,report['current_cloth_game_acceptance'])

if __name__=='__main__':main()
