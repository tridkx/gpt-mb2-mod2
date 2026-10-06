"""Package the installed module and editable source with matching checksums."""
from pathlib import Path
import sys,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
version=sys.argv[1]
module=ROOT/'module/TianxiangT5'
assert ET.parse(module/'SubModule.xml').find('Version').get('value')==version
deliveries=[
    (ROOT/'dist/TianxiangT5_Mod.zip',[(p,'TianxiangT5/'+p.relative_to(module).as_posix()) for p in module.rglob('*') if p.is_file()]),
    (ROOT/'dist/TianxiangT5_Source.zip',[(p,p.relative_to(ROOT).as_posix()) for p in
        [ROOT/'source/TianxiangT5_Rigged.blend',ROOT/'source/TianxiangT5_Rigged.fbx',ROOT/'README.md',*sorted((ROOT/'tex').glob('*.png'))]]),
]
for archive,files in deliveries:
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for file,name in files:z.write(file,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None,archive
        for file,name in files:assert z.read(name)==file.read_bytes(),name
print(f'{version}: module and editable source archives verified.')
