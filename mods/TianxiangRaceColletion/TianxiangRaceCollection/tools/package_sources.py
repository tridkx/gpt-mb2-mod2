"""Deliver complete editable component projects without duplicating workspace sources."""
from pathlib import Path
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[1];C=R.parent
W=next(p for p in R.parents if (p/'tools/project_paths.py').is_file())
cfg=json.loads((R/'mod.json').read_text());entries={}
def add(p):
    p=p.resolve();assert p.is_relative_to(W) and p.is_file()
    name=p.relative_to(W).as_posix()
    if p==R/'reports/source_delivery_validation.json':return
    assert not any(part in ['build','dist','__pycache__','obj'] for part in p.relative_to(W).parts)
    if name in entries:assert entries[name]==p
    entries[name]=p
for rel in cfg['source_files']:add(R/rel)
for ident in json.loads((R/'tools/components.json').read_text()):
    P=C/ident;member=json.loads((P/'mod.json').read_text())
    for rel in member['source_files']:add(P/rel)
    for folder in ['tex','module']:
        for p in (P/folder).rglob('*'):
            if p.is_file():add(p)
    for p in (P/'reports').glob('user_acceptance*.json'):add(p)
    for rel in member.get('shared_source_files',[]):add(W/rel)
for rel in ['AGENTS.md','tools/project_paths.py','tools/package_delivery.py','tools/install_release.ps1']:add(W/rel)
archive=R/'dist'/('TianxiangRaceCollection_Source.zip');temporary=archive.with_suffix('.zip.tmp')
guide='# Tianxiang Race Collection source workspace\n\nKeep the mods/ and tools/ directory hierarchy. Editable Blend/FBX and adjacent tex/ are inside each component project under mods/TianxiangRaceColletion/.\n\nFrom the extracted workspace root run:\n\n    python mods/TianxiangRaceColletion/TianxiangRaceCollection/tools/build_collection.py\n\nFull usage and prerequisites: mods/TianxiangRaceColletion/TianxiangRaceCollection/README.md. External Blender, game assets, .NET and mbtool binaries are not bundled.\n'
with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr('README.md',guide)
    for name,p in sorted(entries.items()):z.write(p,name)
with zipfile.ZipFile(temporary) as z:
    assert z.testzip() is None
    for name,p in entries.items():assert z.read(name)==p.read_bytes(),name
report=dict(status='pass',components=9,files=len(entries)+1,
    source_layout='Full workspace hierarchy; nine original editable projects with adjacent source/tex plus complete component modules and shared tools',
    all_archive_entries_byte_verified=True)
(R/'reports/source_delivery_validation.json').write_text(json.dumps(report,indent=2))
report_path=R/'reports/source_delivery_validation.json'
with zipfile.ZipFile(temporary,'a',compression=zipfile.ZIP_DEFLATED) as z:z.write(report_path,report_path.relative_to(W).as_posix())
with zipfile.ZipFile(temporary) as z:
    assert z.testzip() is None
    assert z.read(report_path.relative_to(W).as_posix())==report_path.read_bytes()
temporary.replace(archive)
print('COMPLETE_COLLECTION_SOURCE_VERIFIED',len(entries),'files',archive.stat().st_size)
