"""Read-only audit of native cloth payloads and the current Mingyu TPAC.

This does not cook cloth or establish the engine meaning of undocumented GUIDs.
Exit 1 means the candidate is missing data found in both native cloth examples.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord')
PROBE = ROOT / 'build/cloth_probe/NativeClothProbe.dll'
PAYLOAD = 'b97e0f10-df49-4666-8f1d-ada6630d4b4e'


def probe(path, *names):
    result = subprocess.run(['dotnet', str(PROBE), str(path), *names],
                            check=True, capture_output=True, encoding='utf-8')
    return json.loads(result.stdout)


def audit():
    native = GAME / 'Modules/Native/EmAssetPackages'
    package = ROOT / 'module/ShengxiuCollection/AssetPackages/sx_mingyu.tpac'
    current = probe(package, 'sx_mingyu_head', 'sx_mingyu_body', 'sx_mingyu_legs')
    tassels = probe(native / 'crafting/crafting.tpac',
                   'spear_banner_16', 'spear_banner_17', 'spear_blade_19')
    proxy = probe(native / 'armor666/armor666.tpac', 'clo_battania_shoulder_strap_cloak')
    missing = []
    for mm in current:
        for mesh in mm['meshes']:
            if 'uses_cloth_simulation' not in mesh['Flags']:
                continue
            has_payload = any(s['TypeGuid'] == PAYLOAD and
                              s['OwnerGuid'] == mesh['Guid'] for s in mm['segments'])
            if not has_payload:
                missing.append({'metamesh': mm['Name'], 'mesh': mesh['Name'],
                                'lod': mesh['Lod'], 'mesh_guid': mesh['Guid'],
                                'editor_bones': mesh['edit_bones'],
                                'runtime_skin_data_size': mesh['SkinDataSize']})
    assert all(any(s['TypeGuid'] == PAYLOAD for s in mm['segments'])
               for mm in tassels if mm['Name'] != 'spear_blade_19')
    assert any(s['TypeGuid'] == PAYLOAD for s in proxy[0]['segments'])
    assert not any(s['TypeGuid'] == PAYLOAD for mm in tassels
                   if mm['Name'] == 'spear_blade_19' for s in mm['segments'])
    result = {
        'status': 'missing_native_cloth_payload' if missing else 'structure_present',
        'final_package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
        'payload_type_guid': PAYLOAD,
        'missing_direct_cloth_meshes': missing,
        'native_direct_tassels_and_rigid_control': tassels,
        'native_skinned_simulation_proxy': proxy,
        'current_package': current,
        'interpretation': 'Strong evidence of missing cloth preprocessed data, not a proven engine diagnosis. Native direct tassels and a skinned cloak simulation proxy have this segment; the rigid blade does not. The current builder emits no such segment. Native proxy also has editor bone data; current skinned cloth has none.',
        'limitations': 'Undocumented payload format; no native solver run. No native payload may be copied to unrelated geometry. Presence alone does not validate constraints, indices, mapping or dynamics.',
        'official_reference': 'https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/',
        'game_dynamic_verified': False,
    }
    path = ROOT / 'reports/cloth_payload_diagnosis.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(result['status'], 'missing meshes:', len(missing))
    return result


if __name__ == '__main__':
    raise SystemExit(1 if audit()['missing_direct_cloth_meshes'] else 0)
