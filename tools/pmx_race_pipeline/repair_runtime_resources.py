"""Repair invalid BC resources and separate native-style simulation drivers."""
from pathlib import Path
import json,sys,shutil,subprocess,hashlib,uuid,concurrent.futures
import numpy as np
from PIL import Image
from context import SERIES,config,workspace_root
from driver_probe import prepare_driver_probe
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
PATCH=SERIES/'build/runtime_resource_patch/RuntimeResourcePatch.dll'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    result=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf8',errors='replace')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    return result.stdout
def repair(root):
    c=config(root);b=root/'build';w=workspace_root(root);prefix=c['prefix'];p=root/'module'/c['id']/'AssetPackages'/(prefix+'.tpac')
    if (root/'reports/runtime_resource_fix.json').exists():return
    baseline=b/'runtime_resource_fix/v0.1.1';baseline.mkdir(parents=True,exist_ok=True)
    if (baseline/p.name).exists():shutil.copy2(baseline/p.name,p)
    oldhash=sha(p);shutil.copy2(p,baseline/p.name)
    for name in ['release_validation.json','cloth_diagnostics.json','game_acceptance.json','final_visibility.json']:
        if (root/'reports'/name).exists():shutil.copy2(root/'reports'/name,baseline/name)
    oldgeo=[{f.name:f.read_bytes() for f in (b/f'final_export_lod{lod}/geo').glob('*.bin')} for lod in range(4)]
    oldbones=(root/'reports/final_skeleton.json').read_bytes();spec=json.loads((b/'spec.json').read_text());changed=[]
    sys.path[:0]=[str(w/'tools/asset_helpers/pipeline'),'D:/mb-tools/py'];from convert_textures import encode_mips
    from bcencode import decode_bc1,decode_bc3,decode_bc5
    before_cloth=None
    if c['cloth_enabled']:
        before_cloth=json.loads((b/'mapped_final/inspection.json').read_text());run(['dotnet',PATCH,'native-driver',p,b/'native_role_fixed.tpac',prefix]);shutil.copy2(b/'native_role_fixed.tpac',p)
        prepare_driver_probe(root)
    for texture in spec['textures']:
        if texture['width']%4==0 and texture['height']%4==0:continue
        oldsize=[texture['width'],texture['height']]
        # Re-encode from the preserved source PNG rather than lossy decoded BC.
        materials=json.loads((root/'reports/material_names.json').read_text());matname=next(k for k,v in materials.items() if v['textures']['0']==texture['name']);source=json.loads((root/'tex/materials.json').read_text());image=Image.open(root/'tex'/source[matname[len(prefix)+1:]]['diffuse']).convert('RGBA')
        size=(1<<(image.width-1).bit_length(),1<<(image.height-1).bit_length());pixels=np.array(image.resize(size,Image.Resampling.LANCZOS));encoded,mips=encode_mips(pixels,texture['format']);Path(texture['blob']).write_bytes(encoded);texture.update(width=size[0],height=size[1],mips=mips)
        donor={'output':str(b/'valid_texture.tpac'),'packageGuid':str(uuid.uuid5(uuid.NAMESPACE_URL,c['id']+'/bc-size-fix')),'templates':spec['templates'],'textures':[texture]};(b/'valid_texture_spec.json').write_text(json.dumps(donor,indent=2));run([MB,'build',b/'valid_texture_spec.json']);run(['dotnet',PATCH,'replace-texture',p,b/'texture_size_fixed.tpac',b/'valid_texture.tpac',texture['name']]);shutil.copy2(b/'texture_size_fixed.tpac',p);changed.append({'texture':texture['name'],'before':oldsize,'after':list(size),'source_png_preserved':True})
    (b/'spec.json').write_text(json.dumps(spec,indent=2))
    for lod in range(4):
        folder=b/f'final_export_lod{lod}';run([MB,'exportmod',p,folder,lod]+(['--all-mips'] if lod==0 else []))
        assert all((folder/'geo'/name).read_bytes()==data for name,data in oldgeo[lod].items()),'Geometry stream changed'
    run([MB,'skeljson',p,prefix+'_skeleton',root/'reports/final_skeleton.json']);assert (root/'reports/final_skeleton.json').read_bytes()==oldbones
    pack=json.loads((b/'final_export_lod0/pack.json').read_text());assert all(t['width']%4==0 and t['height']%4==0 for t in pack['textures'])
    for texture in pack['textures']:
        blob=(b/'final_export_lod0'/texture['file']).read_bytes();assert blob==(b/'tex'/(texture['name']+'.bc')).read_bytes();width,height=texture['width'],texture['height']
        for level,(offset,length) in enumerate(zip(texture['mipOffset'],texture['mipSize'])):
            rgba={'DXT1':decode_bc1,'DXT5':decode_bc3,'BC5':decode_bc5}[texture['format']](blob[offset:offset+length],width,height)
            if level==0 and texture['format']!='BC5':Image.fromarray(rgba).save(b/'final_export_lod0/tex'/(texture['name']+'.png'))
            width=max(1,width//2);height=max(1,height//2)
    if before_cloth:
        run(['dotnet',b/'mapped_patch/MappedClothPatch.dll','--inspect',p,prefix+'_body',prefix+'_cloth_proxy',b/'mapped_final']);after=json.loads((b/'mapped_final/inspection.json').read_text())
        for mesh in before_cloth[0]['meshes']:mesh['Flags']=[f for f in mesh['Flags'] if f!='force_enable_cloth']
        assert before_cloth[0]==after[0]
        old=before_cloth[1];new=after[1];assert old['segments']==new['segments'] and new['body']=='' and new['meshes'][0]['Flags']==[];assert old['meshes'][0]['ClothingMaterial']==new['meshes'][0]['ClothingMaterial']
        metadata=json.loads(run(['dotnet',w/'tools/AssetTool/AssetTool.dll','inspect',p,prefix+'_cloth_proxy']))[0];driver=metadata['meshes'][0];assert metadata['UnknownString']=='' and driver['Flags']==[] and not any(driver[k] for k in ['UnknownBool1','UnknownBool2','UnknownBool3'])
    audit=json.loads(run([sys.executable,'-X','utf8','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',p,'--cloth-vertex-alpha']));assert audit['status']=='pass';(root/'reports/package_audit.json').write_text(json.dumps(audit,indent=2))
    visible=json.loads(run(['dotnet',w/'tools/AssetTool/AssetTool.dll','visibility',p]));(root/'reports/final_visibility.json').write_text(json.dumps(visible,indent=2))
    report={'status':'pass','version':'v0.1.2','date':'2026-10-15','baseline_package_sha256':oldhash,'final_package_sha256':sha(p),'all_lod_geometry_bytes_unchanged':True,'skeleton_bytes_unchanged':True,'cloth_payloads_mappings_and_materials_unchanged':True,'native_driver_role':c['cloth_enabled'],'texture_dimensions_fixed':changed,'gpu_texture_contract':'Top-level BC width and height multiples of four; all encoded mip levels decoded successfully','game_verified':False,'hair_fix_requires_user_retest':c['cloth_enabled']}
    (root/'reports/runtime_resource_fix.json').write_text(json.dumps(report,indent=2));history=root/'reports/history';history.mkdir(exist_ok=True)
    for name in ['hair_proxy_visibility_fix.json','hair_proxy_visibility_preview.json']:
        old=root/'reports'/name
        if old.exists():shutil.move(str(old),str(history/('v0.1.1_'+name)))
    old=json.loads((root/'reports/release_validation.json').read_text());old.update(version='v0.1.2',date='2026-10-15',baseline_package_sha256=oldhash,baseline_reason='Native driver role and BC texture runtime compatibility repair; all geometry and physics streams preserved',final_package_sha256=report['final_package_sha256'],repair_validation='reports/runtime_resource_fix.json');(root/'reports/release_validation.json').write_text(json.dumps(old,indent=2))
    c.update(version='v0.1.2',native_driver_role=bool(c['cloth_enabled']));(root/'tools/model_config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
    import xml.etree.ElementTree as ET
    desc=p.parents[1]/'SubModule.xml';tree=ET.parse(desc);tree.getroot().find('Version').set('value','v0.1.2');ET.indent(tree);tree.write(desc,encoding='utf-8',xml_declaration=True)
    (root/'reports/game_acceptance.json').write_text(json.dumps({'version':'v0.1.2','status':'pending_user_runtime_retest','package_sha256':sha(p),'game_launched_by_assistant':False,'required_scenes':['character_creation_loading','hair_closeup','hair_motion']},indent=2))
    print('RUNTIME_RESOURCE_REPAIRED',root.name,flush=True)
if __name__=='__main__':
    rows=[p for p in SERIES.iterdir() if (p/'tools/model_config.json').exists() and p.name!='EmilieRace' and (config(p).get('cloth_enabled') or p.name in ['LisaRace','NoelleRace'])]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(repair,rows))
    (SERIES/'reports/runtime_resource_fix.json').write_text(json.dumps([{'id':p.parent.parent.name,**json.loads(p.read_text())} for p in SERIES.glob('*/reports/runtime_resource_fix.json')],indent=2))
