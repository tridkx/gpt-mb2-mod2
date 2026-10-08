"""Recheck relocated editable files against their retained release inputs."""
import bpy,hashlib,json
from pathlib import Path
collection=Path(__file__).resolve().parents[1]
project=collection/'sets/TianxiangXuezhi'
script=project/'tools/verify_source.py'
code=script.read_text(encoding='utf-8')
# Reuse all actual Blend/FBX/native-bind checks, without treating later edits
# to the user's external original FBX as a migration change.
namespace={'__file__':str(script),'__name__':'grouped_source_check'}
exec(compile(code[:code.index("original=Path(cfg['original_directory'])")],str(script),'exec'),namespace)
report=namespace['report'];changed_external=[]
baseline=json.loads((project/'reports/input_preservation.json').read_text(encoding='utf-8'))
for row in baseline['files']:
    file=project/row['copy'];digest=hashlib.sha256(file.read_bytes()).hexdigest()
    assert digest==row['sha256'],file
    original=Path(row['original'])
    if original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest()!=digest:changed_external.append(str(original))
report.update(retained_input_hashes_match_release=True,external_inputs_changed_since_release=changed_external,scope='relocated editable source and retained first-release inputs; external user edits left untouched')
(collection/'reports/grouped_source_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('GROUPED_SOURCE_VERIFIED',report)
