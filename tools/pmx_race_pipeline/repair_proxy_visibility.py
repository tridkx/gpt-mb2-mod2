"""Minimal driver-material repair, with exact preservation checks against v0.1.0."""
from pathlib import Path
import json,sys,subprocess,hashlib,shutil,uuid,struct,concurrent.futures
import numpy as np
from PIL import Image
from context import SERIES,config,workspace_root
from proxy_material import add_material
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,encoding='utf8',errors='replace').stdout
def mesh_payload(data):
    # One proxy submesh: retain every stream byte, omitting only material identity.
    assert struct.unpack_from('<I',data,8)[0]==1
    offset=12
    for k in range(3):
        size=struct.unpack_from('<I',data,offset)[0];offset+=4+size
        if k==0:offset+=4 # LOD
    return data[offset:]
def repair(root):
    c=config(root);prefix=c['prefix'];b=root/'build';w=workspace_root(root);p=root/'module'/c['id']/'AssetPackages'/(prefix+'.tpac');baseline=b/'hair_proxy_fix/v0.1.0';baseline.mkdir(parents=True,exist_ok=True)
    assert not (root/'reports/hair_proxy_visibility_fix.json').exists(),'Already repaired'
    shutil.copy2(p,baseline/p.name)
    for name in ['release_validation.json','material_names.json','game_acceptance.json','final_preview_manifest.json']:
        if (root/'reports'/name).exists():shutil.copy2(root/'reports'/name,baseline/name)
    old_report=json.loads((baseline/'release_validation.json').read_text());assert old_report['final_package_sha256']==sha(p)
    old_geometry=[{f.name:f.read_bytes() for f in (b/f'final_export_lod{lod}/geo').glob('*.bin')} for lod in range(4)]
    old_textures={f.name:f.read_bytes() for f in (b/'final_export_lod0/tex').glob('*.bin')}
    old_cloth=json.loads((b/'mapped_final/inspection.json').read_text());old_bones=(root/'reports/final_skeleton.json').read_bytes()
    spec=json.loads((b/'spec.json').read_text());donor={k:spec[k] for k in ['templates']};donor.update(output=str(b/'proxy_visibility_donor.tpac'),packageGuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'gpt-mb2-mod2/'+c['id']+'/invisible-cloth-proxy')),textures=[],materials=[])
    name=add_material(root,donor);(b/'proxy_visibility_spec.json').write_text(json.dumps(donor,indent=2));run([MB,'build',b/'proxy_visibility_spec.json'])
    run(['dotnet',SERIES/'build/proxy_visibility_patch/ProxyVisibilityPatch.dll',p,b/'proxy_visibility_donor.tpac',b/'proxy_visibility_fixed.tpac',prefix]);shutil.copy2(b/'proxy_visibility_fixed.tpac',p)
    spec['textures'].extend(donor['textures']);spec['materials'].extend(donor['materials']);(b/'spec.json').write_text(json.dumps(spec,indent=2))
    for lod in range(4):
        folder=b/f'final_export_lod{lod}';run([MB,'exportmod',p,folder,lod]+(['--all-mips'] if lod==0 else []))
        for filename,raw in old_geometry[lod].items():
            current=(folder/'geo'/filename).read_bytes()
            assert (mesh_payload(raw)==mesh_payload(current)) if filename==prefix+'_cloth_proxy.bin' else raw==current,(c['id'],filename,lod)
    assert all((b/'final_export_lod0/tex'/filename).read_bytes()==raw for filename,raw in old_textures.items())
    run([MB,'skeljson',p,prefix+'_skeleton',root/'reports/final_skeleton.json']);assert (root/'reports/final_skeleton.json').read_bytes()==old_bones
    run(['dotnet',b/'mapped_patch/MappedClothPatch.dll','--inspect',p,prefix+'_body',prefix+'_cloth_proxy',b/'mapped_final'])
    assert old_cloth==json.loads((b/'mapped_final/inspection.json').read_text()),'Cloth mapping, flags, settings or payload changed'
    pack=json.loads((b/'final_export_lod0/pack.json').read_text());texture=next(t for t in pack['textures'] if t['name']==prefix+'_proxy_zero')
    sys.path.insert(0,'D:/mb-tools/py');from bcencode import decode_bc3
    blob=(b/'final_export_lod0'/texture['file']).read_bytes();width=texture['width'];height=texture['height']
    for mip,(offset,size) in enumerate(zip(texture['mipOffset'],texture['mipSize'])):
        decoded=decode_bc3(blob[offset:offset+size],width,height);assert decoded[:,:,3].max()==0
        if mip==0:Image.fromarray(decoded).save(b/'final_export_lod0/tex'/(texture['name']+'.png'))
        width=max(1,width//2);height=max(1,height//2)
    proxy=next(m for m in pack['meshes'] if m['name']==prefix+'_cloth_proxy');assert all(m['material']==name for m in proxy['submeshes'])
    audit=json.loads(run([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',p,'--cloth-vertex-alpha']));assert audit['status']=='pass';(root/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
    report=dict(status='pass',date='2026-10-15',version='v0.1.1',baseline_package_sha256=old_report['final_package_sha256'],final_package_sha256=sha(p),proxy_material=name,all_texture_mips_alpha_zero=True,all_lod_body_geometry_bytes_unchanged=True,proxy_stream_bytes_unchanged=True,cloth_payloads_mappings_and_settings_unchanged=True,skeleton_bytes_unchanged=True,original_encoded_textures_unchanged=True,game_verified=False)
    (root/'reports/hair_proxy_visibility_fix.json').write_text(json.dumps(report,indent=2))
    old_report.update(version='v0.1.1',date='2026-10-15',baseline_package_sha256=report['baseline_package_sha256'],baseline_reason='Material-only driver visibility repair; all geometry, original textures, skeleton and cloth bytes preserved',final_package_sha256=report['final_package_sha256'],repair_validation='reports/hair_proxy_visibility_fix.json',game_test_verified=False);(root/'reports/release_validation.json').write_text(json.dumps(old_report,indent=2))
    c['version']='v0.1.1';(root/'tools/model_config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
    import xml.etree.ElementTree as ET
    descriptor=p.parents[1]/'SubModule.xml';tree=ET.parse(descriptor);tree.getroot().find('Version').set('value','v0.1.1');ET.indent(tree);tree.write(descriptor,encoding='utf-8',xml_declaration=True)
    (root/'reports/game_acceptance.json').write_text(json.dumps({'version':'v0.1.1','status':'pending_user_hair_artifact_retest','package_sha256':report['final_package_sha256'],'game_launched_by_assistant':False,'previous_feedback':'Overall positive; moving single-color hair patches reported, notably Ningguang and Weisina.'},indent=2))
    preview=root/'reports/final_preview_manifest.json'
    if preview.exists():
        data=json.loads(preview.read_text());data.update(package_sha256=report['final_package_sha256'],geometry_previews_reused_after_exact_stream_comparison=True);preview.write_text(json.dumps(data,indent=2))
    print('PROXY_REPAIRED',c['id'],flush=True)
    return {'id':c['id'],**report}
if __name__=='__main__':
    requested=sys.argv[1:];roots=[p for p in SERIES.iterdir() if (p/'tools/model_config.json').exists() and config(p).get('cloth_enabled') and p.name!='EmilieRace' and not (p/'reports/hair_proxy_visibility_fix.json').exists() and (not requested or p.name in requested)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(repair,roots))
    results=[{'id':p.parent.parent.name,**json.loads(p.read_text())} for p in SERIES.glob('*/reports/hair_proxy_visibility_fix.json')]
    (SERIES/'reports/hair_proxy_visibility_fix.json').write_text(json.dumps(results,indent=2))
