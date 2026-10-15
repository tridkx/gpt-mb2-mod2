"""Apply the native mapped-render owner defaults as well as driver defaults."""
import json,subprocess,shutil,hashlib
from context import SERIES,config,workspace_root
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for path in SERIES.glob('*/reports/runtime_resource_fix.json'):
    root=path.parent.parent;c=config(root);proof=json.loads(path.read_text())
    if not proof['native_driver_role']:continue
    p=root/'module'/c['id']/'AssetPackages'/(c['prefix']+'.tpac');b=root/'build';before={str(f.relative_to(b)):f.read_bytes() for lod in range(4) for f in (b/f'final_export_lod{lod}/geo').glob('*.bin')}
    subprocess.run(['dotnet',str(SERIES/'build/runtime_resource_patch/RuntimeResourcePatch.dll'),'native-driver',str(p),str(b/'mapped_owner_role_fixed.tpac'),c['prefix']],check=True);shutil.copy2(b/'mapped_owner_role_fixed.tpac',p)
    for lod in range(4):subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(p),str(b/f'final_export_lod{lod}'),str(lod)]+(['--all-mips'] if lod==0 else []),check=True,capture_output=True)
    assert all((b/name).read_bytes()==raw for name,raw in before.items())
    subprocess.run(['dotnet',str(b/'mapped_patch/MappedClothPatch.dll'),'--inspect',str(p),c['prefix']+'_body',c['prefix']+'_cloth_proxy',str(b/'mapped_final')],check=True,capture_output=True)
    w=workspace_root(root);data=json.loads(subprocess.run(['dotnet',str(w/'tools/AssetTool/AssetTool.dll'),'inspect',str(p),c['prefix']+'_body'],capture_output=True,text=True,check=True).stdout)[0]
    for mesh in data['meshes']:
        if 'uses_cloth_simulation' in mesh['Flags']:assert mesh['Flags']==['uses_cloth_simulation'] and not any(mesh[k] for k in ['UnknownBool1','UnknownBool2','UnknownBool3'])
    proof.update(final_package_sha256=sha(p),native_mapped_owner_role=True);path.write_text(json.dumps(proof,indent=2))
    report=root/'reports/release_validation.json';r=json.loads(report.read_text());r['final_package_sha256']=sha(p);report.write_text(json.dumps(r,indent=2))
    report=root/'reports/game_acceptance.json';r=json.loads(report.read_text());r['package_sha256']=sha(p);report.write_text(json.dumps(r,indent=2))
    print('NATIVE_RENDER_OWNER_VERIFIED',root.name,flush=True)
(SERIES/'reports/runtime_resource_fix.json').write_text(json.dumps([{'id':p.parent.parent.name,**json.loads(p.read_text())} for p in SERIES.glob('*/reports/runtime_resource_fix.json')],indent=2))
