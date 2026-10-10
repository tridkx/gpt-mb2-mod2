import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
R=Path(__file__).resolve().parents[1];WS=R.parents[1]
sys.path.insert(0,str(WS/'tools/asset_helpers/tools'))
from georead import read_geo
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
module=R/'module/FeifengScaleTest';package=module/'AssetPackages/ffs.tpac'
old=R/'dist/FeifengScaleTest_v0.1.1_Mod.zip'
if not old.exists():old=R/'dist/FeifengScaleTest_Mod.zip'
with zipfile.ZipFile(old) as z:
 descriptor=E.fromstring(z.read('FeifengScaleTest/SubModule.xml'))
 assert descriptor.find('Version').get('value')=='v0.1.1'
 baseline=hashlib.sha256(z.read('FeifengScaleTest/AssetPackages/ffs.tpac')).hexdigest()
assert sha(package)==baseline,'Geometry/material package must remain byte-identical'
items=E.parse(module/'ModuleData/items.xml')
for part in ['head','body','legs']:
 assert items.find("Item[@id='ffs_C_%s']"%part).get('mesh')==items.find("Item[@id='ffs_D_%s']"%part).get('mesh')=='ffs_a_'+part
rig=json.loads((R/'reports/human_skeleton.json').read_text())
# Check the actual final TPAC head pieces have vertices bound exclusively to head.
groups=[g for p in (R/'build/final_export0/geo').glob('*.bin') for g in read_geo(p)]
head=[g for g in groups if g['name'].startswith('ffs_a_head_') and g['material'] in {'ffs_mat_4','ffs_mat_5','ffs_mat_7','ffs_mat_8'}]
assert head
for g in head:assert np.all(g['bi'][g['bw']>0]==13)
result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(R/'tools/verify_runtime.ps1'),'-RuntimeDll',str(module/'bin/Win64_Shipping_Client/FeifengScaleTest.dll')],capture_output=True,text=True)
assert result.returncode==0,result.stdout+result.stderr
report=dict(version='v0.1.2',status='pass',scope='offline diagnostic setup; no native engine execution',final_package_sha256=sha(package),baseline_v0_1_1_package_sha256=baseline,runtime_dll_sha256=sha(module/'bin/Win64_Shipping_Client/FeifengScaleTest.dll'),identical_C_D_meshes=True,head_only_vertex_groups=[g['name'] for g in head],compiled_checks=result.stdout.strip(),phase_seconds=[6,12,6,12],bone=13,bone_name='head',scale=[2,2,2],force_update=False,once_profile='C',continuous_profile='D',callback='OnPreDisplayMissionTick',player_only=True,game_verified=False,previous_user_feedback=dict(version='v0.1.1',date='2026-10-10',visibility='A/B visible in inventory and battle screenshots',scale='logged bone segment lengths unchanged; previous origin-only logs do not exclude skinning-only scaling'),api_reference='https://apidoc.bannerlord.com/v/1.3.14/class_tale_worlds_1_1_mount_and_blade_1_1_m_b_agent_visuals.html',native_wrapper='forwards sparse arrays and their count; implementation in native engine is not exposed')
(R/'reports/single_bone_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('SINGLE_BONE_DIAGNOSTIC_OFFLINE_PASS')
