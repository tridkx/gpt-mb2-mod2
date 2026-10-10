"""Compare final meshes, textures and skeleton to user-accepted v0.1.1."""
from pathlib import Path
import json,sys,zipfile,subprocess,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];WS=R.parents[1];B=R/'build'
sys.path[:0]=[str(WS/'tools/asset_helpers/tools'),str(WS/'tools/asset_helpers/previewer')]
from georead import read_geo
from baker.skeleton import parse_skeljson
MB='D:/mb-tools/mbtool/bin/Release/net9.0/mbtool.exe'
baseline=B/'accepted_v0.1.1.tpac'
with zipfile.ZipFile(R/'dist/YueQingShuRace_v0.1.1_Mod.zip') as z:
    baseline.write_bytes(z.read('YueQingShuRace/AssetPackages/yqs.tpac'))
old=json.loads((R/'reports/history/v0.1.1/release_validation.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(baseline)==old['final_package_sha256']
rows=[]
for lod in range(4):
    folder=B/f'accepted_export_lod{lod}'
    subprocess.run([MB,'exportmod',str(baseline),str(folder),str(lod)]+(['--all-mips'] if lod==0 else []),check=True,capture_output=True)
    def meshes(folder):return {m['name']:m for f in (folder/'geo').glob('*.bin') for m in read_geo(f)}
    before=meshes(folder);after=meshes(B/f'final_export_lod{lod}');assert before.keys()==after.keys()
    maxerror=0
    for name,a in before.items():
        b=after[name]
        for key in ['idx','bi','bw','uv']:
            assert np.array_equal(a[key],b[key]),(lod,name,key,'accepted baseline changed')
        assert a['pos'].shape==b['pos'].shape
        error=float(np.max(np.abs(a['pos']-b['pos'])));maxerror=max(maxerror,error);assert error<2e-6,(lod,name,error)
    rows.append(dict(lod=lod,mesh_count=len(before),max_position_error_m=maxerror,indices_uv_weights_identical=True))
subprocess.run([MB,'skeljson',str(baseline),'yqs_skeleton',str(B/'accepted_skeleton.json')],check=True,capture_output=True)
before=parse_skeljson(json.loads((B/'accepted_skeleton.json').read_text()));after=parse_skeljson(json.loads((R/'reports/final_skeleton.json').read_text()))
assert before['names']==after['names'] and np.array_equal(before['parent'],after['parent']) and np.array_equal(before['restWorld'],after['restWorld'])
before=json.loads((B/'accepted_export_lod0/pack.json').read_text());after=json.loads((B/'final_export_lod0/pack.json').read_text())
assert [t['name'] for t in before['textures']]==[t['name'] for t in after['textures']]
for a,b in zip(before['textures'],after['textures']):
    assert (B/'accepted_export_lod0'/a['file']).read_bytes()==(B/'final_export_lod0'/b['file']).read_bytes()
report=dict(status='pass',version='v0.2.0',baseline_version='v0.1.1',baseline_package_sha256=sha(baseline),final_package_sha256=sha(R/'module/YueQingShuRace/AssetPackages/yqs.tpac'),lods=rows,source_skeleton_identical=True,all_texture_mips_identical=True,user_feedback='User accepted v0.1.1 appearance; scope of tested gameplay unspecified',game_cloth_verified=False)
(R/'reports/preservation_validation.json').write_text(json.dumps(report,indent=2));print('ACCEPTED_APPEARANCE_PRESERVED',rows)
