"""Read archive contents without importing models or modifying their sources."""
from pathlib import Path
import zipfile,json

def entry_name(info):
    name=info.filename
    if not info.flag_bits&2048:
        try:name=name.encode('cp437').decode('gbk')
        except (UnicodeEncodeError,UnicodeDecodeError):pass
    return name.replace('\\','/')

def inventory(folder):
    rows=[]
    for path in sorted(Path(folder).glob('*.zip')):
        with zipfile.ZipFile(path) as z:
            entries=[entry_name(i) for i in z.infolist()]
        rows.append({'archive':path.name,'size_mb':round(path.stat().st_size/1e6,2),'models':[n for n in entries if Path(n).suffix.lower() in ['.pmx','.pmd','.fbx','.obj','.blend']],'readmes':[n for n in entries if Path(n).suffix.lower()=='.txt']})
    return rows

if __name__=='__main__':
    import sys
    print(json.dumps(inventory(sys.argv[1]),ensure_ascii=False,indent=2))
