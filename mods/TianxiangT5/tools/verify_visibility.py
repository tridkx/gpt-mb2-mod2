"""Regress opacity/cloth-alpha conflict against both final TPAC revisions."""
from pathlib import Path
import json,subprocess,tempfile,sys
ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT.parents[1]/'tools/AssetTool/AssetTool.dll'
PACK=ROOT/'module/TianxiangT5/AssetPackages/tx5.tpac'

def audit(path):
    p=subprocess.run(['dotnet',str(TOOL),'visibility',str(path)],check=True,capture_output=True,text=True)
    return json.loads(p.stdout)

baseline='v1.1.0'
with tempfile.TemporaryDirectory(prefix='tx5_visibility_') as temp:
    before_path=Path(temp)/'before.tpac'
    previous=subprocess.run(['git','show',f'{baseline}:module/TianxiangT5/AssetPackages/tx5.tpac'],
                            cwd=ROOT,check=True,capture_output=True)
    before_path.write_bytes(previous.stdout)
    before=audit(before_path)
after=audit(PACK)
old_materials={m['Guid']:m for m in before['materials']}
materials={m['Guid']:m for m in after['materials']}
old_meshes={m['Name']:m for m in before['meshes']}
meshes={m['Name']:m for m in after['meshes']}
assert len(materials)==len(old_materials)==9
assert set(meshes)==set(old_meshes) and len(meshes)==56
previously_clipped=[]
materials_only='--materials-only' in sys.argv
unchanged_meshes=0
unchanged_colors=0
for guid,m in materials.items():
    assert 'disable_vertex_color_alpha' in m['ShaderMaterialFlags'],m['Name']
    old=old_materials[guid]
    assert set(m['ShaderMaterialFlags'])==set(old['ShaderMaterialFlags'])|{'disable_vertex_color_alpha'}
    assert m['AlphaTest']==old['AlphaTest'] and m['BlendMode']==old['BlendMode']
for name,m in meshes.items():
    old=old_meshes[name]
    if not materials_only:assert m==old,f'Mesh or cloth data changed: {name}'
    for key in ['Name','Lod','Flags','Material']:assert m[key]==old[key],(name,key)
    unchanged_meshes+=int(m==old)
    unchanged_colors+=int(m['ColorsSHA256']==old['ColorsSHA256'])
    mat=old_materials[m['Material']]
    if 'alpha_test' in mat['ShaderMaterialFlags'] and m['AlphaMax']/255 < mat['AlphaTest']:
        # Every diffuse pixel has alpha <= 1, so all these vertices clip in
        # the non-simulated rendering path when vertex alpha is not disabled.
        previously_clipped.append(name)
assert len(previously_clipped)>=20
cloth=[m['Name'] for m in meshes.values() if 'uses_cloth_simulation' in m['Flags']]
assert len(cloth)==3
MB=r'D:\mb-tools\mbtool\bin\Release\net9.0\mbtool.exe'
checks={}
for cmd in ['metacheck','mataudit']:
    p=subprocess.run([MB,cmd,str(PACK)],check=True,capture_output=True,text=True)
    checks[cmd]=p.stdout.strip()
result={'baseline_version':baseline,'materials_ignore_vertex_opacity':9,'mesh_equality_required':not materials_only,
        'submeshes_vertex_colors_unchanged':unchanged_colors,
        'submeshes_geometry_weights_and_cloth_metadata_unchanged':unchanged_meshes,
        'previously_fully_clipped_submeshes':previously_clipped,
        'cloth_submeshes_preserved':cloth,'asset_checks':checks,'game_visibility_verified':False}
report='visibility_validation_materials.json' if materials_only else 'visibility_validation.json'
(ROOT/'reports'/report).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
