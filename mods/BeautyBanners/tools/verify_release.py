"""Verify final TPAC pixels, banner and sprite references, IDs and preserved inputs."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from paths import ROOT, MODULE, BUILD, MOD_ID, VERSION, GAME, NATIVE, ASSET_TOOL, MBTOOL, GROUP_ID, PORTRAITS, CATEGORY
from prepare_assets import fit

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(*args):
    return subprocess.check_output([str(x) for x in args], encoding='utf-8')

def main():
    package = MODULE / 'AssetPackages/beauty_banners.tpac'
    checks = []
    def require(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    info = json.loads(run('dotnet', ASSET_TOOL, 'inspect', package))
    (ROOT / 'reports/final_assets.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    require(len(info['assets']) == 3, 'Exactly two textures and one material in the final package')
    asset_guids = {x['Guid'].lower() for x in info['assets']}
    require(len(asset_guids) == 3, 'Independent nonduplicate asset GUIDs')
    material = info['materials'][0]
    native_reference = json.loads((ROOT / 'reports/native_material_reference.json').read_text(encoding='utf-8'))
    require(material['Name'] == 'bb_portrait_icons' and material['shader'] == native_reference['shader'],
            'Portrait material references the installed native simple_shader')
    require(material['BlendMode'] == 'modulate' and material['AlphaTest'] == 0 and material['ShaderMaterialFlags'] == [],
            'Color material preserves texture RGB and soft alpha; no monochrome banner shader')
    require(len(material['textures']) == 1 and material['textures']['0'].lower() in asset_guids,
            'Diffuse binding resolves inside this final package')
    metacheck = run(MBTOOL, 'metacheck', package)
    require('checksum ok=3 bad=0' in metacheck and 'metadata identical=3 differ=0 noSerializer=0' in metacheck,
            'Every final asset checksum and metadata roundtrip passes')
    (ROOT / 'reports/tpac_roundtrip.txt').write_text(metacheck, encoding='utf-8')
    run(MBTOOL, 'exportmod', package, BUILD / 'final_export')
    exported = json.loads((BUILD / 'final_export/pack.json').read_text(encoding='utf-8'))
    final_images = {}
    texture_by_name = {x['Name']: x for x in info['textures']}
    for tex in exported['textures']:
        blob = (BUILD / 'final_export' / tex['file']).read_bytes()
        expected_image = Image.open(ROOT / 'tex' / (tex['name'] + '.png')).convert('RGBA')
        require(tex['format'] == 'R8G8B8A8_UNORM' and tex['mipCount'] == 1 and tex['arrayCount'] == 1,
                tex['name'] + ': RGBA atlas format and single mip/array')
        require(blob == expected_image.tobytes(), tex['name'] + ': final decoded pixels exactly equal the source atlas')
        require(hashlib.sha256(blob).hexdigest().upper() == texture_by_name[tex['name']]['pixel_sha256'],
                tex['name'] + ': independent pixel hash matches final package inspector')
        require('has_alpha' in tex['systemFlags'] and 'ignore_alpha' not in tex['flags'],
                tex['name'] + ': alpha channel enabled')
        final_images[tex['name']] = Image.frombytes('RGBA', (tex['width'], tex['height']), blob)
    provenance = json.loads((ROOT / 'input/provenance.json').read_text(encoding='utf-8'))
    atlas = final_images['bb_portrait_atlas']
    for index, (name, _, _) in enumerate(PORTRAITS):
        original = ROOT / 'input' / (name + '_original.png')
        require(sha(original) == provenance[name]['sha256'], name + ': original approved image unchanged')
        require(original.read_bytes() == (ROOT / 'source' / (name + '.png')).read_bytes(), name + ': editable source is byte-identical')
        art = Image.open(original).convert('RGBA')
        require(atlas.crop((index * 1024, 0, (index + 1) * 1024, 1024)).tobytes() == fit(art, (1024, 1024), 32).tobytes(),
                name + ': correct atlas slot without crop, recolor or deformation')
        alpha = np.asarray(art)[:, :, 3]
        require(np.min(alpha) == 0 and np.max(alpha) >= 250, name + ': transparent background and opaque figure present')
    require(atlas.crop((3072, 0, 4096, 1024)).getbbox() is None and atlas.crop((0, 1024, 4096, 4096)).getbbox() is None,
            'All thirteen unused atlas slots are fully transparent')
    descriptor = ET.parse(MODULE / 'SubModule.xml')
    require(descriptor.find('Id').get('value') == MOD_ID and descriptor.find('Version').get('value') == VERSION,
            'Module ID and version match release')
    require(descriptor.find('Name').get('value').isascii(), 'Launcher display name is English')
    require(descriptor.find('.//XmlName[@id="BannerIcons"]').get('path') == 'banner_icons', 'BannerIcons registered for current game loader')
    require(not list(descriptor.find('SubModules')), 'Data-only module; no runtime DLL or Harmony dependency')
    for xml in MODULE.rglob('*.xml'):
        ET.parse(xml)
    group = ET.parse(MODULE / 'ModuleData/banner_icons.xml').find('.//BannerIconGroup')
    icons = list(group)
    require(group.get('id') == str(GROUP_ID) and group.get('is_pattern') == 'false' and len(icons) == 3, 'Independent player-selectable portrait group')
    require([int(x.get('id')) for x in icons] == [x[2] for x in PORTRAITS] and [int(x.get('texture_index')) for x in icons] == [0, 1, 2],
            'Three icon IDs map to the correct atlas cells')
    require(all(x.get('material_name') == material['Name'] and x.get('is_reserved', 'false') == 'false' for x in icons),
            'All three icons resolve to the material and remain selectable')
    collision_files = []
    for file in (GAME / 'Modules').glob('*/ModuleData/banner_icons.xml'):
        if file.parent.parent.name == MOD_ID:
            continue
        tree = ET.parse(file)
        other_groups = {int(x.get('id')) for x in tree.findall('.//BannerIconGroup')}
        other_ids = {int(x.get('id')) for x in tree.findall('.//Icon')}
        require(GROUP_ID not in other_groups and not ({x[2] for x in PORTRAITS} & other_ids), 'No flag ID conflict with ' + file.parent.parent.name)
        collision_files.append(str(file))
    sprite = ET.parse(MODULE / 'GUI/BeautyBannersSpriteData.xml')
    category = sprite.find('.//SpriteCategory')
    require(category.findtext('Name') == CATEGORY and category.find('AlwaysLoad') is not None,
            'Unique UI sprite category with AlwaysLoad')
    require(CATEGORY + '_1' in texture_by_name, 'UI sheet name matches the game resource loader')
    ui_atlas = final_images[CATEGORY + '_1']
    for part in sprite.findall('.//SpritePart'):
        require(part.findtext('CategoryName') == CATEGORY and part.findtext('SheetID') == '1', 'Sprite category and sheet resolve for ' + part.findtext('Name'))
        x, y, w, h = [int(part.findtext(k)) for k in ['SheetX', 'SheetY', 'Width', 'Height']]
        require(x >= 0 and y >= 0 and x + w <= ui_atlas.width and y + h <= ui_atlas.height, 'Sprite coordinates within final sheet')
        thumb = Image.open(MODULE / 'GUI/SpriteParts' / CATEGORY / (part.findtext('Name') + '.png')).convert('RGBA')
        require(ui_atlas.crop((x, y, x + w, y + h)).tobytes() == thumb.tobytes(), 'Sprite pixels match thumbnail ' + part.findtext('Name'))
    require({x.findtext('Name') for x in sprite.findall('.//GenericSprite')} == {str(x[2]) for x in PORTRAITS}, 'Editor thumbnail names match banner IDs')
    # Compare GUIDs against installed resources without reading heavy pixel data.
    index_path = BUILD / 'installed_guids.tsv'
    run(MBTOOL, 'guidindex', GAME / 'Modules', index_path)
    conflicts = []
    for line in index_path.read_text(encoding='utf-8-sig').splitlines():
        fields = line.split('\t')
        if len(fields) >= 4 and fields[0].lower() in asset_guids and not Path(fields[-1]).is_relative_to(GAME / 'Modules' / MOD_ID):
            conflicts.append(line)
    require(not conflicts, 'No asset GUID collision with any installed module')

    # Offline layout proof from final package pixels; this does not simulate the game shader.
    preview = Image.new('RGB', (1200, 720), '#20232b')
    draw = ImageDraw.Draw(preview)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
    colors = ['#354655', '#20232b', '#3c3e4d']
    for index, (_, label, _) in enumerate(PORTRAITS):
        banner = Image.new('RGBA', (320, 600), colors[index])
        cell = atlas.crop((index * 1024, 0, (index + 1) * 1024, 1024))
        cell = cell.crop(cell.getbbox())
        cell.thumbnail((292, 550), Image.Resampling.LANCZOS)
        banner.alpha_composite(cell, ((320 - cell.width) // 2, (600 - cell.height) // 2))
        preview.paste(banner.convert('RGB'), (40 + index * 400, 45))
        draw.text((40 + index * 400, 660), label, font=font, fill='white')
    preview.save(ROOT / 'reports/final_banner_preview.png')
    report = {'status': 'pass', 'version': VERSION, 'game_version': ET.parse(NATIVE / 'SubModule.xml').find('Version').get('value'),
              'final_package_sha256': sha(package), 'checks': checks, 'checked_banner_files': collision_files,
              'resource_memory_mib': 64.25,
              'module_files': {p.relative_to(MODULE).as_posix(): sha(p) for p in sorted(MODULE.rglob('*')) if p.is_file() and p.name != '.gitkeep'},
              'limitations': ['Game not launched. User must check banner editor thumbnails, RGB tint with white sigil, flags, shields and saving/loading.',
                              'Offline preview shows final decoded artwork placement, not in-game lighting or shader output.']}
    (ROOT / 'reports/release_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {len(checks)} offline checks; {len(report["module_files"])} runtime/source sprite files. Game test remains user-owned.')

if __name__ == '__main__':
    main()
