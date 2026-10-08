"""User-authorized original FBX/OBJ repair with recoverable backups."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];original=Path('D:/dsh-tiandao/天香少女校服8套/02沐风为裳')
backup=original/'backup_before_lash_fix_20261008';backup.mkdir(exist_ok=True)
report=json.loads((ROOT/'reports/original_lash_fix.json').read_text());assert report['status']=='pass'
for name in ['model.fbx','model.obj','parts.json','vfix.json','preview/model_face.png']:
    src=original/name;dst=backup/name
    if src.exists() and not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
assert hashlib.sha256((backup/'model.fbx').read_bytes()).hexdigest()==report['original_input_sha256']
lines=(backup/'model.obj').read_text(encoding='utf-8').splitlines(keepends=True);obj='';changed=0
for i,line in enumerate(lines):
    if line.startswith('o '):obj=line.strip().split()[1]
    if obj=='mesh_04_414907' and line.startswith('vt '):
        fields=line.strip().split();fields[2]=format(1-float(fields[2]),'.8f');lines[i]=' '.join(fields)+'\n';changed+=1
assert changed>0
(original/'model.obj').write_text(''.join(lines),encoding='utf-8')
shutil.copy2(ROOT/'source/OriginalModel_LashFixed.fbx',original/'model.fbx')
parts=json.loads((backup/'parts.json').read_text(encoding='utf-8'))
for part in parts:
    if part['name']=='mesh_04_414907':part.update(uvdir='u+1,v+1',default='u+1,v+1',auto='人工修正睫毛 V 方向；FBX/OBJ 已同步',conf='fixed')
(original/'parts.json').write_text(json.dumps(parts,ensure_ascii=False,indent=2),encoding='utf-8')
vfix=json.loads((backup/'vfix.json').read_text(encoding='utf-8'));vfix['414907']=1
(original/'vfix.json').write_text(json.dumps(vfix,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(ROOT/'build/lash_diagnosis/flipped_lash_v.png',original/'preview/model_face.png')
cfgfile=ROOT/'tools/model_config.json';cfg=json.loads(cfgfile.read_text(encoding='utf-8'));cfg['original_fbx_backup']=str(backup/'model.fbx');cfgfile.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
report.update(installed_directory=str(original),backup_directory=str(backup),obj_uv_entries_changed=changed,original_input_retained=True)
(ROOT/'reports/original_lash_fix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('ORIGINAL_FBX_OBJ_REPAIRED',original,'backup',backup)
