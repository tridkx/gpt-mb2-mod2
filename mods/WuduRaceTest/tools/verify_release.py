"""Audit final TPAC, source fidelity and the actual recruit XSLT replacement."""
import sys,json,hashlib,subprocess,struct
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from lxml import etree as ET
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build';M=R/'module/WuduRaceTest';PKG=M/'AssetPackages/wdr.tpac'
GAME=Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord');MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
sys.path[:0]=[str(WS/'tools/asset_helpers/tools'),str(WS/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
from baker.animation import parse_animjson,q2R,lbs
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,path):
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');path.write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');assert p.returncode==0,(cmd,p.stderr);return p.stdout
run([MB,'metacheck',str(PKG)],R/'reports/metacheck.txt')
run([MB,'mataudit',str(PKG)],R/'reports/mataudit.txt')
visibility=json.loads(run(['dotnet',str(WS/'tools/AssetTool/AssetTool.dll'),'visibility',str(PKG)],R/'reports/visibility.json'))
run([MB,'skeljson',str(PKG),'wdr_skeleton',str(R/'reports/final_skeleton.json')],R/'reports/skeleton_readback.txt')
data=json.loads((R/'reports/final_skeleton.json').read_text());rig=parse_skeljson(data)
native=parse_skeljson(json.loads((R/'reports/human_skeleton.json').read_text()));expected=json.loads((B/'skeleton_spec.json').read_text())
assert rig['names']==native['names'] and np.array_equal(rig['parent'],native['parent'])
assert np.max(abs(np.array([b['rest'] for b in data['bones']])-np.array([b['rest'] for b in expected])))<1e-6
assert np.linalg.norm(rig['restWorld'][0,:3,3]-[0,0,.75])<1e-6
geometry={g['name']:g for g in json.loads((B/'geometry.json').read_text())};allgroups=[];source=np.load(B/'source_positions.npz');maxerror=0
for lod in range(4):
    run([MB,'exportmod',str(PKG),str(B/f'final_export{lod}'),str(lod)],R/'reports'/f'export_lod{lod}.txt')
    groups=[g for p in (B/f'final_export{lod}/geo').glob('*.bin') for g in read_geo(p)];allgroups.extend(groups)
    assert len(groups)==14
    for g in groups:
        assert g['lod']==lod and np.isfinite(g['pos']).all() and np.isfinite(g['uv']).all()
        assert g['bi'].max()<28 and np.all(g['bw'].astype(int).sum(1)==255)
        assert g['idx'].min()>=0 and g['idx'].max()<len(g['pos'])
        rec=geometry[g['name']];buf=Path(rec['geometry']).read_bytes();_,count,indices=struct.unpack_from('<iii',buf);offset=12
        p=np.frombuffer(buf,'<f4',count*3,offset).reshape(-1,3);offset+=count*(3+3+4+2+2)*4+count*4
        bi=np.frombuffer(buf,'u1',count*4,offset).reshape(-1,4);offset+=count*4;bw=np.frombuffer(buf,'u1',count*4,offset).reshape(-1,4)
        assert np.array_equal(p,g['pos']) and np.array_equal(bi,g['bi']) and np.array_equal(bw,g['bw'])
        if rec['part']=='body':
            key=g['name'].split('.lod')[0]+'_p';err=float(cKDTree(source[key]).query(g['pos'])[0].max());maxerror=max(maxerror,err);assert err<1e-6
assert len(allgroups)==56
native_npc=ET.parse(str(GAME/'Modules/SandBoxCore/ModuleData/spnpccharacters.xml'))
transform=ET.XSLT(ET.parse(str(M/'ModuleData/wdr_troops.xslt')));result=transform(native_npc)
orig=native_npc.xpath("//NPCCharacter[@id='imperial_recruit']")[0];troop=result.xpath("//NPCCharacter[@id='imperial_recruit']")[0]
assert troop.get('race')=='wdr_canglan' and troop.get('is_female')=='true' and troop.get('level')==orig.get('level')=='6'
assert [dict(x.attrib) for x in troop.findall('skills/skill')]==[dict(x.attrib) for x in orig.findall('skills/skill')]
assert [x.get('id') for x in troop.findall('upgrade_targets/upgrade_target')]==[x.get('id') for x in orig.findall('upgrade_targets/upgrade_target')]
assert all(x.get('slot','Item0').startswith('Item') for x in troop.findall('Equipments/EquipmentRoster/equipment'))
before=native_npc.xpath("//NPCCharacter[not(@id='imperial_recruit')]");after=result.xpath("//NPCCharacter[not(@id='imperial_recruit')]")
assert len(before)==len(after) and all(ET.tostring(a)==ET.tostring(b) for a,b in zip(before,after))
for path in M.rglob('*.xml'):ET.parse(str(path))
skins=ET.parse(str(M/'ModuleData/skins.xml'));assert len(skins.xpath('//race'))==1 and len(skins.xpath('//skin'))==10
assert all(s.get('skeleton')=='wdr_skeleton' and len(s.findall('deform_keys/deform_key'))==0 for s in skins.xpath('//skin'))
native_skins=ET.parse(str(GAME/'Modules/Native/ModuleData/skins.xml')).xpath("//race[@id='human']/skin")
for skin,baseline in zip(skins.xpath('//skin'),native_skins):
    for tag in ['hair_meshes','beard_meshes']:
        node=skin.find(tag);original=baseline.find(tag)
        assert node is not None,('Required native skin container missing',skin.get('name'),tag)
        assert dict(node.attrib)==dict(original.attrib),('Native skin container attributes changed',tag)
        assert len(node)==1 and node[0].tag==tag.removesuffix('es') and node[0].get('name') is None,('Native zero-index no-hair/no-beard entry required',tag)

for k,v in json.loads((R/'reports/input_hashes.json').read_text()).items():assert sha(R/k)==v
origfolder=Path('D:/dsh-tiandao/五毒少女校服8套/01苍蓝流苏')
for p in (R/'input').iterdir():
    if p.is_file() and p.name!='.gitkeep':assert sha(p)==sha(origfolder/p.name)
for p in (R/'tex').glob('*.png'):assert sha(p)==sha(origfolder/'tex'/p.name)
# Offline prediction checks arithmetic only; native retargeting/IK are not emulated.
animation=parse_animjson(json.loads((R/'reports/run.json').read_text()));assert animation['boneCount']==28 and animation['have'].all()
selected=[g for g in allgroups if g['lod']==0 and g['name'].startswith('wdr_part_')];preview={};inverse=np.linalg.inv(rig['restWorld'])
for frame in range(animation['start'],animation['frames']):
    world=np.zeros_like(inverse)
    for i in range(28):
        local=rig['restLocal'][i].copy();local[:3,:3]=q2R(animation['quat'][i,frame]);parent=rig['parent'][i]
        if parent<0:local[:3,3]+=animation['rootPos'][frame]
        world[i]=local if parent<0 else world[parent]@local
    for g in selected:
        points=lbs(g['pos'],g['bi'],g['bw'],world@inverse);assert np.isfinite(points).all()
        if frame==animation['start']:preview[g['name']]=points
np.savez_compressed(B/'run_preview.npz',**preview)
game_files=[GAME/'Modules/Native/ModuleData/skins.xml',GAME/'Modules/Native/ModuleData/monsters.xml',GAME/'Modules/Native/ModuleData/action_sets.xml',GAME/'Modules/SandBoxCore/ModuleData/spnpccharacters.xml']
report=dict(status='pass',version='v0.1.2',scope='offline structure/source fidelity/XML replacement; game appearance is pending',final_package_sha256=sha(PKG),runtime_dll_sha256=sha(M/'bin/Win64_Shipping_Client/WuduRaceTest.dll'),source_vertex_max_error_m=maxerror,source_height_m=json.loads((R/'reports/source_validation.json').read_text())['total_height_m'],custom_skeleton_bones=28,metameshes=2,mesh_groups=56,lods=4,lod_geometry_identical=True,cloth_enabled=False,intrinsic_armor_added=False,autoresolve_modified=False,other_troops_unchanged=len(before),predicted_run_frames=animation['frames']-animation['start'],game_verified=False,proportions_in_game_verified=False,native_file_hashes={str(p):sha(p) for p in game_files},known_limits=['fixed source face','no cloth or clipping fixes','native animation retargeting and IK unverified','no equipment armor','only imperial_recruit is replaced'])
(R/'reports/release_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
