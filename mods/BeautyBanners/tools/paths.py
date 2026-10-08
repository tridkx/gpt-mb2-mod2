"""Local tool defaults; override them for a different installation."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
BUILD = ROOT / 'build'
MOD_ID = 'BeautyBanners'
VERSION = 'v1.1.0'
MODULE = ROOT / 'module' / MOD_ID
GAME = Path(os.environ.get('BANNERLORD_GAME_ROOT', r'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord'))
NATIVE = GAME / 'Modules' / 'Native'
MBTOOL = Path(os.environ.get('BANNERLORD_MBTOOL', r'D:\mb-tools\mbtool\bin\Release\net9.0\mbtool.exe'))
SHADERS = NATIVE / 'EmAssetPackages/core/shaders/misc/misc.tpac'
CORE_MATERIALS = NATIVE / 'EmAssetPackages/core/core_materials/core_materials.tpac'
UI_TEXTURES = NATIVE / 'AssetPackages/gauntlet_ui.tpac'
ASSET_TOOL = BUILD / 'asset_tool/BannerAssets.dll'
PORTRAITS = [('ol', 'OL Uniform', 7101), ('qipao', 'Satin Qipao', 7102), ('hanfu', 'Elegant Hanfu', 7103)]
GROUP_ID = 71
CATEGORY = 'ui_beautybanners'
WHITE_COLOR_ID = 71001
