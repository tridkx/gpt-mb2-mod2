"""Build color-preserving banner assets; no game or editor launch."""
import json
import subprocess
import uuid
from PIL import Image
from paths import ROOT, BUILD, MODULE, MBTOOL, CORE_MATERIALS, UI_TEXTURES, SHADERS, ASSET_TOOL
from prepare_assets import main as prepare

def run(*args):
    subprocess.run([str(x) for x in args], check=True)

def main():
    prepare()
    BUILD.mkdir(exist_ok=True)
    run('dotnet', 'build', ROOT / 'tools/BannerAssets/BannerAssets.csproj', '--configuration', 'Release',
        '--output', ASSET_TOOL.parent,
        '-p:BaseIntermediateOutputPath=' + str(BUILD / 'asset_tool_obj') + '/')
    probe = subprocess.check_output(['dotnet', str(ASSET_TOOL), 'probe', str(CORE_MATERIALS), str(SHADERS)], encoding='utf-8')
    (ROOT / 'reports/native_material_reference.json').write_text(probe, encoding='utf-8')
    spec = {'output': str(BUILD / 'base.tpac'),
            'packageGuid': str(uuid.uuid5(uuid.NAMESPACE_URL, 'bannerlord/BeautyBanners/package/v1')),
            'templates': {
                'ui_texture': {'tpac': str(UI_TEXTURES), 'name': 'ui_bannericons_1'},
                'banner_material': {'tpac': str(CORE_MATERIALS), 'name': 'custom_banner_icons_01'}},
            'textures': [], 'materials': [], 'meshes': []}
    for filename, name in [('bb_portrait_atlas.png', 'bb_portrait_atlas'), ('ui_beautybanners_1.png', 'ui_beautybanners_1')]:
        image = Image.open(ROOT / 'tex' / filename).convert('RGBA')
        blob = BUILD / (name + '.rgba')
        blob.write_bytes(image.tobytes())
        spec['textures'].append({'name': name, 'template': 'ui_texture', 'blob': str(blob),
            'source': '$BASE/Modules/BeautyBanners/AssetSources/' + filename,
            'width': image.width, 'height': image.height, 'mips': 1, 'format': 'R8G8B8A8_UNORM',
            'flags': ['dont_degrade', 'dont_delay_loading', 'dont_compress'], 'systemFlags': ['has_alpha']})
    spec['materials'] = [{'name': 'bb_portrait_icons', 'template': 'banner_material',
                         'flags': ['two_sided'], 'blendMode': 'modulate', 'alphaTest': 0,
                         'shaderMaterialFlags': [], 'textures': {'0': 'bb_portrait_atlas'},
                         'dropTextureSlots': list(range(1, 10))}]
    spec_path = BUILD / 'spec.json'
    spec_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    run(MBTOOL, 'build', spec_path)
    package = MODULE / 'AssetPackages/beauty_banners.tpac'
    run('dotnet', ASSET_TOOL, 'patch', BUILD / 'base.tpac', SHADERS, package)
    print('Built', package)

if __name__ == '__main__':
    main()
