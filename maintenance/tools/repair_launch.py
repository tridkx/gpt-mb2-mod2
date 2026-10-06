"""Remove the obsolete Jingrenou entries from this local Bannerlord install.

Only the explicitly marked JJRO blocks are removed. Complete byte-for-byte
backups and a hash manifest are kept in this project before applying edits.
"""
from pathlib import Path
import argparse, hashlib, json, re, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
NATIVE=Path(r'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord\Modules\Native\ModuleData')
BACKUP=ROOT/'backups/jingrenou_cleanup_20261006'
TARGETS={'skins.xml':('race','jingrenou'),'action_sets.xml':('action_set','as_jingrenou')}
PATTERN=re.compile(rb'<!--JJRO_BEGIN-->.*?<!--JJRO_END-->',re.S)

def digest(data):return hashlib.sha256(data).hexdigest()

def semantic(tree):
    for e in tree.iter():
        if e.text is not None and not e.text.strip():e.text=None
        if e.tail is not None and not e.tail.strip():e.tail=None
    return ET.tostring(tree)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();plans=[]
    for name,(tag,identifier) in TARGETS.items():
        path=(NATIVE/name).resolve()
        assert path.parent==NATIVE.resolve()
        before=path.read_bytes();blocks=list(PATTERN.finditer(before))
        if not blocks:
            assert b'jingrenou' not in before.lower(),f'Unmarked reference in {name}'
            continue
        assert len(blocks)==1 and b'jingrenou' in blocks[0].group().lower()
        after=PATTERN.sub(b'',before)
        assert b'jingrenou' not in after.lower()
        old_tree=ET.fromstring(before);new_tree=ET.fromstring(after)
        removed=[e for e in old_tree.findall(tag) if e.get('id')==identifier]
        assert len(removed)==1
        old_tree.remove(removed[0])
        assert semantic(old_tree)==semantic(new_tree),f'Unexpected XML changes in {name}'
        plans.append((path,before,after,identifier))
    if not plans:
        print('No active Jingrenou entries remain.');return
    BACKUP.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for path,before,after,identifier in plans:
        backup=BACKUP/path.name
        if backup.exists():assert backup.read_bytes()==before,'Backup already contains a different revision'
        else:backup.write_bytes(before)
        assert backup.read_bytes()==before
        (BACKUP/(path.name+'.cleaned')).write_bytes(after)
        manifest.append({'file':str(path),'removed_id':identifier,'before_sha256':digest(before),'after_sha256':digest(after),'backup':str(backup)})
    (BACKUP/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    if args.apply:
        # Recheck both input files before writing either one.
        assert all(path.read_bytes()==before for path,before,after,identifier in plans)
        for path,before,after,identifier in plans:
            path.write_bytes(after)
            assert path.read_bytes()==after
            ET.parse(path)
    report={'applied':args.apply,'changes':manifest,'game_launch_verified':False,
            'observed_crash':'2026-10-06 10:24, TaleWorlds.Native.dll+0x725eff, read address 0x1f8; last body mesh: jingrenou',
            'historical_match':'2026-10-02 13:04, same native DLL offset, before TianxiangT5 existed'}
    (ROOT/'reports/launch_repair.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
