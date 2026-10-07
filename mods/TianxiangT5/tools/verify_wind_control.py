"""Require all v1.5.0 resource data unchanged except the single wind field."""
from pathlib import Path
import subprocess,json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/wind_control'
config=json.loads((ROOT/'tools/wind_control_config.json').read_text());dll=ROOT/'build/sleeve_tool/bin/SleeveTool.dll'
def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,encoding='utf-8').stdout
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OUT/'baseline.tpac')==config['baseline_package_sha256']
packages={'baseline':OUT/'baseline.tpac','final':OUT/'tx5.tpac'};decoded={};metadata={}
for kind,package in packages.items():
    run(['dotnet',dll,'dump',package,OUT/(kind+'.json')]);decoded[kind]={m['name']:m for m in json.loads((OUT/(kind+'.json')).read_text())}
    metadata[kind]={}
    for owner in ['tx5_head','tx5_body','tx5_legs','tx5_cloth_simulation']:
        folder=OUT/kind/owner;run(['dotnet',dll,'inspect',package,owner,folder]);metadata[kind][owner]=json.loads((folder/'metadata.json').read_text())
a=decoded['baseline'];b=decoded['final'];assert a.keys()==b.keys() and len(a)==57
changes=[]
for name,old in a.items():
    current=b[name]
    if name=='tx5_cloth_simulation':
        assert old['cloth']['Wind']==np.float32(.08) or np.isclose(old['cloth']['Wind'],.08)
        assert current['cloth']['Wind']==0
        current=json.loads(json.dumps(current));current['cloth']['Wind']=old['cloth']['Wind'];assert current==old
        changes.append({'mesh':name,'field':'Wind','before':old['cloth']['Wind'],'after':0})
    else:assert current==old,name
    assert np.all(np.array(b[name]['bw']).sum(1)==255)
    assert np.isfinite(b[name]['pos']).all() and np.array(b[name]['bi']).max()<28
segments=0;fabric=0;mapping=0
for owner,old in metadata['baseline'].items():
    current=json.loads(json.dumps(metadata['final'][owner]))
    if owner=='tx5_cloth_simulation':current['meshes'][0]['ClothingMaterial']['Wind']=old['meshes'][0]['ClothingMaterial']['Wind']
    assert current==old,(owner,'unexpected metadata difference')
    for seg in old['segments']:
        assert (OUT/'baseline'/owner/seg['file']).read_bytes()==(OUT/'final'/owner/seg['file']).read_bytes(),(owner,seg['file'])
        segments+=1;fabric+=seg['type'].startswith('b97');mapping+=seg['type'].startswith('af416')
assert fabric==1 and mapping==3
mbtool='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
for owner in metadata['final']:
    txt=run([mbtool,'segcheck',OUT/'tx5.tpac',owner]);assert 'DIFFERS' not in txt and 'failed' not in txt and 'first diff' not in txt
assettool=ROOT.parents[1]/'tools/AssetTool/AssetTool.dll'
base=json.loads(run(['dotnet',assettool,'visibility',OUT/'baseline.tpac']))
final=json.loads(run(['dotnet',assettool,'visibility',OUT/'tx5.tpac']))
assert base['materials']==final['materials']
for old,current in zip(base['meshes'],final['meshes']):
    if old['Name']=='tx5_cloth_simulation':
        # This digest includes the intentionally modified cloth material.
        assert {k:v for k,v in old.items() if k!='ClothMetadataSHA256'}=={k:v for k,v in current.items() if k!='ClothMetadataSHA256'}
    else:assert old==current
for kind,package in packages.items():run([mbtool,'exportmod',package,OUT/(kind+'_export'),'0','--all-mips'])
texture_hashes={}
for tex in (OUT/'baseline_export/tex').glob('*.bin'):
    assert tex.read_bytes()==(OUT/'final_export/tex'/tex.name).read_bytes();texture_hashes[tex.name]=sha(tex)
assert len(texture_hashes)==11
for lod in [1,2,3]:run([mbtool,'exportmod',OUT/'tx5.tpac',OUT/('lod'+str(lod)),str(lod)])
audit=json.loads(run(['C:/ProgramData/anaconda3/python.exe','C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py',OUT/'tx5.tpac','--cloth-vertex-alpha']));assert audit['status']=='pass'
(ROOT/'reports/wind_control_asset_audit.json').write_text(json.dumps(audit,indent=2))
source_hashes=json.loads((OUT/'source_hashes.json').read_text())
for name,digest in source_hashes.items():assert sha(ROOT/'source'/name)==digest
source=json.loads((ROOT/'reports/wind_control_source_validation.json').read_text());assert source['status']=='pass'
from sleeve_motion import skin_frames,posed
rig=json.loads((ROOT/'reports/human_skeleton.json').read_text());motions=[]
for label in ['idle','run','bow','riding','grip_twohanded_block','grip_twohanded_thrust']:
    anim=json.loads((ROOT/f'reports/{label}.json').read_text());skins,_=skin_frames(rig,anim)
    for skin in skins:
        for mesh in b.values():assert np.isfinite(posed(mesh,skin)).all()
    motions.append({'animation':anim['name'],'frames':len(skins),'all_lods_verified':True})
report={'version':config['version'],'status':'pass','baseline_version':'v1.5.0','baseline_package_sha256':config['baseline_package_sha256'],'final_package_sha256':sha(OUT/'tx5.tpac'),'changed_fields':changes,'unchanged_data_segments':segments,'original_fabric_byte_exact':True,'all_three_mappings_byte_exact':True,'all_geometry_skin_alpha_flags_distances_and_other_parameters_unchanged':True,'all_materials_and_11_full_mip_textures_unchanged':True,'texture_sha256':texture_hashes,'sources_restored_byte_exact':source_hashes,'source_validation':'pass','native_animation_checks':motions,'game_test_verified':False,'baseline_no_stretch_user_reported':True,'limitations':'v1.6.1 is a controlled wind-only test based on v1.5.0. No runtime proof of non-stretching or reduced waving; complete sleeve draping remains unresolved. Do not confuse inherited consistency with solver validation.'}
(ROOT/'reports/wind_control_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['version','status','final_package_sha256','changed_fields','unchanged_data_segments']},indent=2))
