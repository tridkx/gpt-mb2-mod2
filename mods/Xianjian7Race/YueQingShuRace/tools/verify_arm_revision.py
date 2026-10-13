"""Verify final GPU preservation and model-specific corrected arm binding."""
from pathlib import Path
import sys,json,numpy as np,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from workspace_paths import workspace_root
sys.path.insert(0,str(workspace_root(R)/'tools/asset_helpers/previewer'));from baker.skeleton import parse_skeljson
old=parse_skeljson(json.loads((R/'tools/arm_bind_baseline.json').read_text()));new=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()));assert old['names']==new['names'] and np.array_equal(old['parent'],new['parent']);rows=[];allowed=[]
for pre in ['l','r']:
 for name,a,b in [('upperarm_twist','upperarm_twist','foretwist'),('upperarm_twist1','upperarm_twist','foretwist'),('foretwist','foretwist','hand'),('foretwist1','foretwist','hand')]:
  i=new['names'].index(pre+'_'+name);allowed.append(i);axis=new['restWorld'][i,:3,0];direction=new['restWorld'][new['names'].index(pre+'_'+b),:3,3]-new['restWorld'][new['names'].index(pre+'_'+a),:3,3];angle=float(np.degrees(np.arccos(np.clip(axis@direction/np.linalg.norm(axis)/np.linalg.norm(direction),-1,1))));assert angle<.001;rows.append(dict(bone=pre+'_'+name,final_axis_error_degrees=angle))
assert np.max(abs(old['restWorld'][:,:3,3]-new['restWorld'][:,:3,3]))<2e-6;keep=[i for i in range(28) if i not in allowed];assert np.max(abs(old['restWorld'][keep]-new['restWorld'][keep]))<2e-6
# Recover the same accepted baseline on a clean rebuild; caches are not source assets.
import zipfile,subprocess
baseline=R/'build/baseline_v0.3.0.tpac'
if not baseline.exists():
 archive=R/'dist/YueQingShuRace_v0.3.0_Mod.zip';assert archive.exists(),'Keep v0.3.0 Mod ZIP for baseline checks'
 with zipfile.ZipFile(archive) as z:baseline.write_bytes(z.read('YueQingShuRace/AssetPackages/yqs.tpac'))
for lod in range(4):
 folder=R/'build/baseline_v0.3.0_exports'/f'lod{lod}'
 if not (folder/'pack.json').exists():subprocess.run(['D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe','exportmod',str(baseline),str(folder),str(lod)]+(['--all-mips'] if lod==0 else []),check=True,stdout=subprocess.DEVNULL)
for lod in range(4):
 a=R/'build/baseline_v0.3.0_exports'/f'lod{lod}';b=R/'build'/f'final_export_lod{lod}'
 aa={p.name:p for p in (a/'geo').glob('*.bin')};bb={p.name:p for p in (b/'geo').glob('*.bin')};assert aa.keys()==bb.keys()
 for name,p in aa.items():assert p.read_bytes()==bb[name].read_bytes(),name
 ap=json.loads((a/'pack.json').read_text());bp=json.loads((b/'pack.json').read_text());assert ap['materials']==bp['materials']
 if lod==0:
  for tex in ap['textures']:assert (a/tex['file']).read_bytes()==(b/tex['file']).read_bytes()
baseline_cloth=R/'build/arm_baseline_cloth';baseline_cloth.mkdir(exist_ok=True)
subprocess.run(['dotnet',str(R/'build/cloth_probe/NativeClothProbe.dll'),str(baseline),'yqs_body','--dump-segments',str(baseline_cloth)],check=True,stdout=subprocess.DEVNULL)
cloth_count=0
for p in baseline_cloth.glob('*.bin'):
 assert p.read_bytes()==(R/'build/cloth_final'/p.name).read_bytes(),('Cloth changed',p.name)
 if not p.name.endswith('.edit.bin'):cloth_count+=1
assert cloth_count==18
report=dict(cloth_payloads_byte_identical_to_v0_3_0=cloth_count,status='pass',version=json.loads((R/'tools/model_config.json').read_text())['version'],final_package_sha256=hashlib.sha256((R/'module/YueQingShuRace/AssetPackages/yqs.tpac').read_bytes()).hexdigest(),bones=rows,joint_positions_and_limb_lengths_preserved=True,non_arm_bind_world_frames_preserved=True,all_lod_gpu_streams_byte_identical=True,materials_all_texture_mips_preserved=True,game_retest_pending=True)
(R/'reports/arm_binding_validation.json').write_text(json.dumps(report,indent=2));print('ARM_BIND_REVISION_VERIFIED',rows)
