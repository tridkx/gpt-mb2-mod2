"""Finalize direct-hair configuration, immutable stream evidence and scoped UI logs."""
from pathlib import Path
import json,hashlib,shutil,subprocess,concurrent.futures
from context import SERIES,config,workspace_root
from scaffold import scaffold
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def finish(root):
    c=config(root);b=root/'build';p=root/'reports/direct_hair_cloth.json';proof=json.loads(p.read_text());assert proof['all_lod_visible_geometry_bytes_unchanged']
    bypart={}
    for row in proof['meshes']:bypart.setdefault(row['mesh'].split('.lod')[0],[]).append(row)
    equivalents=[]
    for name,rows in bypart.items():
        assert {r['lod'] for r in rows}=={0,1,2,3}
        equivalents.append({'part':name,'lods':[0,1,2,3],'same_payload':len({r['sha256'] for r in rows})==1})
    # The same direct packet and identical visible streams need one numerical run.
    allsame=all(g['same_payload'] for g in equivalents);c.update(version='v0.1.3',cloth_mode='direct',direct_diagnostic_lods=[0] if allsame else [0,1,2,3]);(root/'tools/model_config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
    proof.update(version='v0.1.3',date='2026-10-15',lod_payload_equivalence=equivalents,representative_diagnostic_lods=c['direct_diagnostic_lods'],runtime_material_probe=True);p.write_text(json.dumps(proof,indent=2))
    history=root/'reports/history';history.mkdir(exist_ok=True)
    for name in ['runtime_resource_fix.json','native_driver_input_validation.json','mapped_cloth.json','proxy_source_validation.json']:
        old=root/'reports'/name
        if old.exists():shutil.move(str(old),str(history/('v0.1.2_'+name)))
    baseline=b/'direct_hair_trial/v0.1.2/release_validation.json';r=json.loads(baseline.read_text());r.update(version='v0.1.3',date='2026-10-15',baseline_package_sha256=proof['baseline_package_sha256'],final_package_sha256=proof['package_sha256'],baseline_reason='Replace proxy-mapped hair with direct UV-bearing visible cloth; all four visible geometry streams unchanged',cloth_mode='direct',proxy_simulation_vertices=0,cloth_render_groups=len(proof['meshes']),repair_validation='reports/direct_hair_cloth.json');r['limitations']=[v for v in r['limitations'] if not v.startswith('Mapped cloth')];r['limitations'].insert(0,'Direct CPU cloth is approximate; native solver, rendering and motion appearance require user game testing.');(root/'reports/release_validation.json').write_text(json.dumps(r,indent=2))
    (root/'reports/game_acceptance.json').write_text(json.dumps({'version':'v0.1.3','status':'pending_user_direct_hair_retest','game_launched_by_assistant':False,'previous_feedback':'Hair patches in v0.1.2 disappear when game cloth simulation is disabled.','required_scenes':['cloth_enabled_hair_closeup','hair_motion','lod_distances']},indent=2))
    scaffold(root)
    scope=root/'reports/ui_scope_validation.json';d=json.loads(scope.read_text());d.update(readonly_hair_material_probe=True,hair_probe_source_sha256=sha(root/'tools/UIRuntime/HairRuntimeProbe.cs'));scope.write_text(json.dumps(d,indent=2))
    audit=json.loads(subprocess.run(['C:/ProgramData/anaconda3/python.exe','-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',str(root/'module'/c['id']/'AssetPackages'/(c['prefix']+'.tpac')),'--cloth-vertex-alpha'],capture_output=True,text=True,check=True).stdout);assert audit['status']=='pass';(root/'reports/package_audit.json').write_text(json.dumps(audit,indent=2));print('DIRECT_HAIR_READY',root.name,allsame,flush=True)
if __name__=='__main__':
    roots=[p for p in SERIES.iterdir() if (p/'reports/direct_hair_cloth.json').exists()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(finish,roots))
    (SERIES/'reports/direct_hair_cloth.json').write_text(json.dumps([{'id':p.name,**json.loads((p/'reports/direct_hair_cloth.json').read_text())} for p in roots],indent=2))
