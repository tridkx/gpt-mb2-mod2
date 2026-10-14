"""Run shared report-mode diagnostics on an isolated final candidate module.

The normal workspace module and its release configuration remain unchanged.
Mapped-body unsupported results remain incomplete, never converted to pass.
"""
from pathlib import Path
import json,shutil,subprocess,sys,hashlib
from workspace_paths import workspace_root
R=Path(__file__).resolve().parents[1];W=workspace_root(R)

def main():
    stage=R/'build/outer_driver_diagnostics';stage.mkdir(exist_ok=True)
    cfg=json.loads((R/'tools/outer_driver_mod.json').read_text())
    (stage/'mod.json').write_text(json.dumps(cfg,indent=2)+'\n')
    inputs={cfg['package']:R/'build/mapped_candidate.tpac',
        'module/YueQingShuRace/ModuleData/cloth_bodies.xml':R/'module/YueQingShuRace/ModuleData/cloth_bodies.xml',
        'reports/final_skeleton.json':R/'reports/final_skeleton.json'}
    for name in ['ui_neutral_female','run','riding']:inputs['reports/'+name+'.json']=R/'reports'/(name+'.json')
    for relative,p in inputs.items():
        target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    shutil.copytree(R/'build/cloth_probe',stage/'build/cloth_probe',dirs_exist_ok=True)
    candidate=R/'build/mapped_candidate.tpac';before=hashlib.sha256(candidate.read_bytes()).hexdigest()
    result=subprocess.run([sys.executable,'-B','-X','utf8',str(W/'tools/cloth_simulator/pipeline.py'),'--project',str(stage)])
    report=json.loads((stage/'reports/cloth_diagnostics.json').read_text())
    expected={'within_thresholds':0,'needs_review':1,'incomplete':2}
    if report['status']=='error' or result.returncode!=expected.get(report['status']):
        raise RuntimeError('Shared diagnostic execution failed: '+report['status'])
    assert before==hashlib.sha256(candidate.read_bytes()).hexdigest()
    shutil.copy2(stage/'reports/cloth_diagnostics.json',R/'reports/experiments/outer_driven_layers_2026-10-14/cloth_diagnostics.json')
    print('FINAL_CANDIDATE_DIAGNOSTICS',report['status'],before)

if __name__=='__main__':main()
