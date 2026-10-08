"""Pack landscape artwork while retaining the original approved portraits."""
import hashlib
import json
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from paths import ROOT, MODULE, PORTRAITS, CATEGORY, MOD_ID, VERSION, GROUP_ID, WHITE_COLOR_ID, ARTWORK, UI_SIZE

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_xml(path, root):
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)

def fit(image, size, padding):
    # Asset packing only: keep the approved composition, proportions and alpha.
    out = Image.new('RGBA', size)
    copy = image.copy()
    copy.thumbnail((size[0] - 2 * padding, size[1] - 2 * padding), Image.Resampling.LANCZOS)
    out.paste(copy, ((size[0] - copy.width) // 2, (size[1] - copy.height) // 2))
    return out

def main():
    provenance = json.loads((ROOT / 'input/provenance.json').read_text(encoding='utf-8'))
    landscape = json.loads((ROOT / 'input/landscape_provenance.json').read_text(encoding='utf-8'))
    for folder in ['source', 'tex', 'reports', 'module/BeautyBanners/GUI/SpriteParts/' + CATEGORY]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    atlas = Image.new('RGBA', (4096, 4096))
    ui_atlas = Image.new('RGBA', UI_SIZE)
    manifest = []
    for name, _, _ in PORTRAITS:
        original = ROOT / 'input' / (name + '_original.png')
        if sha256(original) != provenance[name]['sha256']:
            raise ValueError('Approved original changed: ' + name)
        preserved = ROOT / 'source' / (name + '.png')
        if original.read_bytes() != preserved.read_bytes():
            raise ValueError('Preserved portrait source changed: ' + name)
        landscape_input = ROOT / 'input' / (name + '_landscape_v1.png')
        if sha256(landscape_input) != landscape[name]['sha256']:
            raise ValueError('Landscape input changed: ' + name)
        source = ROOT / 'source' / (name + '_landscape.png')
        if landscape_input.read_bytes() != source.read_bytes():
            raise ValueError('Preserved landscape source changed: ' + name)
    for index, item in enumerate(ARTWORK):
        name, label, icon_id = item['name'], item['label'], item['icon_id']
        original = ROOT / item['input']
        if sha256(original) != item['sha256']:
            raise ValueError('Approved artwork changed: ' + name)
        source = ROOT / item['source']
        if source.exists() and source.read_bytes() != original.read_bytes():
            raise ValueError('Source differs from approved input: ' + name)
        shutil.copy2(original, source)
        art = Image.open(source).convert('RGBA')
        cell = fit(art, (1024, 1024), 32)
        atlas.paste(cell, ((index % 4) * 1024, (index // 4) * 1024))
        thumb = fit(art, (100, 100), 2)
        thumb.save(MODULE / 'GUI/SpriteParts' / CATEGORY / (str(icon_id) + '.png'))
        ui_atlas.paste(thumb, (4 + index * 108, 4))
        manifest.append({'name': name, 'label': label, 'icon_id': icon_id, 'texture_index': index,
                         'input': original.relative_to(ROOT).as_posix(),
                         'source': source.relative_to(ROOT).as_posix(),
                         'original_sha256': sha256(original), 'kind': item['kind'],
                         'size': list(art.size)})
    atlas.save(ROOT / 'tex/bb_portrait_atlas.png')
    ui_atlas.save(ROOT / 'tex/ui_beautybanners_1.png')
    (ROOT / 'source/artwork_manifest.json').write_text(json.dumps({
        'version': VERSION, 'group_id': GROUP_ID, 'atlas_grid': [4, 4], 'portraits': manifest,
        'provenance': 'Nine user-approved illustrations generated with built-in image_gen; prior artwork preserved.',
        'processing': 'Proportional packing only; no crop, recoloring or deformation.',
        'white_color_id': WHITE_COLOR_ID
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    root = ET.Element('base', {'type': 'string'})
    data = ET.SubElement(root, 'BannerIconData')
    group = ET.SubElement(data, 'BannerIconGroup', {'id': str(GROUP_ID), 'name': '{=bb_portraits}美女旗帜', 'is_pattern': 'false'})
    for index, item in enumerate(ARTWORK):
        ET.SubElement(group, 'Icon', {'id': str(item['icon_id']), 'material_name': 'bb_portrait_icons', 'texture_index': str(index)})
    colors = ET.SubElement(data, 'BannerColors')
    ET.SubElement(colors, 'Color', {'id': str(WHITE_COLOR_ID), 'hex': '0xffffffff',
                                  'player_can_choose_for_background': 'true',
                                  'player_can_choose_for_sigil': 'true'})
    write_xml(MODULE / 'ModuleData/banner_icons.xml', root)

    sprite = ET.Element('SpriteData')
    categories = ET.SubElement(sprite, 'SpriteCategories')
    category = ET.SubElement(categories, 'SpriteCategory')
    ET.SubElement(category, 'Name').text = CATEGORY
    ET.SubElement(category, 'AlwaysLoad')
    ET.SubElement(category, 'SpriteSheetCount').text = '1'
    ET.SubElement(category, 'SpriteSheetSize', {'ID': '1', 'Width': str(UI_SIZE[0]), 'Height': str(UI_SIZE[1])})
    parts = ET.SubElement(sprite, 'SpriteParts')
    sprites = ET.SubElement(sprite, 'Sprites')
    for index, item in enumerate(ARTWORK):
        icon_id = item['icon_id']
        part = ET.SubElement(parts, 'SpritePart')
        for key, value in [('SheetID', 1), ('Name', icon_id), ('Width', 100), ('Height', 100),
                           ('SheetX', 4 + index * 108), ('SheetY', 4), ('CategoryName', CATEGORY)]:
            ET.SubElement(part, key).text = str(value)
        generic = ET.SubElement(sprites, 'GenericSprite')
        ET.SubElement(generic, 'Name').text = str(icon_id)
        ET.SubElement(generic, 'SpritePartName').text = str(icon_id)
    write_xml(MODULE / 'GUI/BeautyBannersSpriteData.xml', sprite)
    cfg = ET.Element('Config')
    ET.SubElement(ET.SubElement(cfg, 'SpriteCategory', {'Name': CATEGORY}), 'AlwaysLoad')
    write_xml(MODULE / 'GUI/SpriteParts/Config.xml', cfg)

    descriptor = ET.Element('Module')
    for key, value in [('Name', 'Beauty Banners'), ('Id', MOD_ID), ('Version', VERSION),
                       ('DefaultModule', 'false'), ('ModuleCategory', 'Singleplayer'),
                       ('Official', 'false'), ('ModuleType', 'Community')]:
        ET.SubElement(descriptor, key, {'value': value})
    deps = ET.SubElement(descriptor, 'DependedModules')
    for name in ['Native', 'SandBoxCore', 'Sandbox']:
        ET.SubElement(deps, 'DependedModule', {'Id': name})
    ET.SubElement(descriptor, 'SubModules')
    xmls = ET.SubElement(descriptor, 'Xmls')
    node = ET.SubElement(xmls, 'XmlNode')
    ET.SubElement(node, 'XmlName', {'id': 'BannerIcons', 'path': 'banner_icons'})
    write_xml(MODULE / 'SubModule.xml', descriptor)
    # English fallback with Chinese localization, using the game's text convention.
    strings = ET.Element('strings')
    ET.SubElement(strings, 'string', {'id': 'bb_portraits', 'text': 'Beauty Banners'})
    write_xml(MODULE / 'ModuleData/beauty_strings.xml', strings)
    textnode = ET.SubElement(xmls, 'XmlNode')
    ET.SubElement(textnode, 'XmlName', {'id': 'GameText', 'path': 'beauty_strings'})
    write_xml(MODULE / 'SubModule.xml', descriptor)
    translation = ET.Element('base', {'type': 'string'})
    ET.SubElement(ET.SubElement(translation, 'tags'), 'tag', {'language': '简体中文'})
    ET.SubElement(ET.SubElement(translation, 'strings'), 'string', {'id': 'bb_portraits', 'text': '美女旗帜'})
    write_xml(MODULE / 'ModuleData/Languages/CNs/beauty_strings.xml', translation)
    language = ET.Element('LanguageData', {'id': '简体中文', 'name': '简体中文',
                          'subtitle_extension': 'zh-HANS', 'supported_iso': 'zh-HANS,zh,zho,chi,zh-cn,zh-sg'})
    ET.SubElement(language, 'LanguageFile', {'xml_path': 'CNs/beauty_strings.xml'})
    write_xml(MODULE / 'ModuleData/Languages/CNs/language_data.xml', language)
    print('Prepared nine artworks, 4x4 color atlas, nine UI sprites and module XML.')

if __name__ == '__main__':
    main()
