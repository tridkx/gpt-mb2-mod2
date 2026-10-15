"""Preserve v0.1.2 and verify direct hair streams before changing delivery."""
from pathlib import Path
import json,shutil,sys,hashlib
from context import SERIES,config,workspace_root
from direct_hair import build_direct_hair,run
def trial(root):
    c=config(root);b=root/'build';prefix=c['prefix'];p=root/'module'/c['id']/'AssetPackages'/(prefix+'.tpac');backup=b/'direct_hair_trial/v0.1.2';backup.mkdir(parents=True,exist_ok=True)
    if not (backup/p.name).exists():shutil.copy2(p,backup/p.name)
    before={(lod,f.name):f.read_bytes() for lod in range(4) for f in (b/f'final_export_lod{lod}/geo').glob('*.bin') if f.name!=prefix+'_cloth_proxy.bin'}
    old=json.loads((b/'mapped_final/inspection.json').read_text());proxy=next(m for m in old if m['Name']==prefix+'_cloth_proxy');c['direct_cloth_material']=proxy['meshes'][0]['ClothingMaterial'];(root/'tools/model_config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
    for name in ['release_validation.json','cloth_diagnostics.json','game_acceptance.json']:
        if not (backup/name).exists():shutil.copy2(root/'reports'/name,backup/name)
    report=build_direct_hair(root,backup/p.name)
    for lod in range(4):
        folder=b/f'final_export_lod{lod}'
        assert folder.resolve().parent==b.resolve() and folder.name in ['final_export_lod0','final_export_lod1','final_export_lod2','final_export_lod3']
        shutil.rmtree(folder)
        run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',p,folder,lod]+(['--all-mips'] if lod==0 else []))
        assert all((folder/'geo'/name).read_bytes()==raw for (level,name),raw in before.items() if level==lod),'Visible geometry or UV changed'
    pack=json.loads((b/'final_export_lod0/pack.json').read_text());assert {m['name'] for m in pack['meshes']}=={prefix+'_body',prefix+'_hidden'}
    w=workspace_root(root)
    run(['dotnet',b/'mapped_patch/MappedClothPatch.dll','--inspect',p,prefix+'_body',prefix+'_body',b/'direct_hair_final']);inspection=json.loads((b/'direct_hair_final/inspection.json').read_text())[0]
    assert inspection['ClothMetamesh']=='00000000-0000-0000-0000-000000000000'
    assert len(inspection['segments'])==len(report['meshes'])
    expected={p['guid']:p['sha256'] for p in report['meshes']};assert all(s['TypeGuid']=='b97e0f10-df49-4666-8f1d-ada6630d4b4e' and expected[s['OwnerGuid']]==s['sha256'] for s in inspection['segments'])
    sys.path.insert(0,'D:/mb-tools/py');from bcencode import decode_bc1,decode_bc3,decode_bc5
    from PIL import Image
    for texture in pack['textures']:
        blob=(b/'final_export_lod0'/texture['file']).read_bytes();width,height=texture['width'],texture['height']
        for level,(offset,size) in enumerate(zip(texture['mipOffset'],texture['mipSize'])):
            rgba={'DXT1':decode_bc1,'DXT5':decode_bc3,'BC5':decode_bc5}[texture['format']](blob[offset:offset+size],width,height)
            if level==0 and texture['format']!='BC5':Image.fromarray(rgba).save(b/'final_export_lod0/tex'/(texture['name']+'.png'))
            width=max(1,width//2);height=max(1,height//2)
    names=root/'reports/material_names.json';materials=json.loads(names.read_text());materials.pop(prefix+'_proxy_invisible',None);names.write_text(json.dumps(materials,indent=2))
    specpath=b/'spec.json';spec=json.loads(specpath.read_text());spec['textures']=[t for t in spec['textures'] if t['name']!=prefix+'_proxy_zero'];spec['materials']=[m for m in spec['materials'] if m['name']!=prefix+'_proxy_invisible'];specpath.write_text(json.dumps(spec,indent=2))
    report.update(all_lod_visible_geometry_bytes_unchanged=True,baseline_package_sha256=hashlib.sha256((backup/p.name).read_bytes()).hexdigest());(root/'reports/direct_hair_cloth.json').write_text(json.dumps(report,indent=2));print('DIRECT_HAIR_VERIFIED',root.name,len(report['meshes']),flush=True)
if __name__=='__main__':
    import concurrent.futures
    roots=[SERIES/identity for identity in sys.argv[1:]] if sys.argv[1:] else [p for p in SERIES.iterdir() if (p/'tools/model_config.json').exists() and p.name!='EmilieRace' and config(p).get('cloth_enabled')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(trial,roots))
