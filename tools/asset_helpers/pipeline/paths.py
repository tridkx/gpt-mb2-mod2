# -*- coding: utf-8 -*-
"""外部路径探测 —— 不硬编码盘符/用户名。

按工作区约定：引用外部程序或目录时**先探测再使用**（环境变量 → 候选列表 → PATH），
全都失败才报错，并明确告诉用户怎么配。

可用环境变量覆盖（优先级最高）：
    MB2_GAME_DIR   骑马与砍杀2 游戏根目录（含 Modules/ 与 modding_resources/）
    MB_TOOLS_DIR   bannerlord-tpac-toolkit 仓库根（含 mbtool/ 与 py/）

用法：
    from paths import find_game, find_mbtool
    GAME = find_game()          # 找不到抛 SystemExit 并给出配置提示
    MB   = find_mbtool()
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_GAME_ENV = ("MB2_GAME_DIR", "BANNERLORD_DIR", "MB2_DIR")
_TOOLS_ENV = ("MB_TOOLS_DIR", "MBTOOL_DIR")
_GAME_REL = Path("steamapps/common/Mount & Blade II Bannerlord")
_MBTOOL_REL = Path("mbtool/bin/Release/net9.0/mbtool.exe")
_MBTOOL_REL_WIN = Path("mbtool/bin/Release/net9.0/mbtool.exe")


def _env_path(names) -> Path | None:
    for n in names:
        v = os.environ.get(n)
        if v:
            p = Path(v).expanduser()
            if p.exists():
                return p
    return None


def _drive_roots():
    """可能的盘符根（Windows）：C:\\ ~ H:\\；非 Windows 上退化成 / 与 /mnt/*。"""
    if os.name == "nt":
        for letter in "CDEFGH":
            d = Path(f"{letter}:/")
            if d.exists():
                yield d
    else:
        yield Path("/")
        for name in ("mnt", "media", "run/media"):
            base = Path("/") / name
            if base.exists():
                yield from [p for p in base.iterdir() if p.is_dir()]


def _steam_libraries():
    """从 Steam 的 libraryfolders.vdf 里解析出所有库目录（比猜盘符可靠）。"""
    cands = []
    for root in _drive_roots():
        for sub in ("Steam", "SteamLibrary", "Program Files (x86)/Steam",
                    ".steam/steam", ".local/share/Steam"):
            vdf = root / sub / "steamapps" / "libraryfolders.vdf"
            if vdf.is_file():
                cands.append(vdf)
    for vdf in cands:
        try:
            txt = vdf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in txt.splitlines():
            line = line.strip()
            if '"path"' in line:
                parts = line.split('"')
                if len(parts) >= 4:
                    p = Path(parts[3].replace("\\\\", "\\"))
                    if p.exists():
                        yield p


def find_game(required: bool = True) -> Path | None:
    """定位 Bannerlord 游戏根目录。"""
    p = _env_path(_GAME_ENV)
    if p:
        return p
    cands = []
    for lib in _steam_libraries():
        cands.append(lib / "steamapps/common/Mount & Blade II Bannerlord")
    for root in _drive_roots():
        cands.append(root / _GAME_REL)
        for sub in ("SteamLibrary", "Games", "Steam"):
            cands.append(root / sub / _GAME_REL)
    for c in cands:
        if (c / "Modules").is_dir():
            return c
    if required:
        raise SystemExit(
            "★ 找不到 Bannerlord 游戏目录。请设置环境变量后再跑：\n"
            "    set MB2_GAME_DIR=<游戏根目录>      (Windows cmd)\n"
            "    $env:MB2_GAME_DIR='<游戏根目录>'   (PowerShell)\n"
            "    export MB2_GAME_DIR=<游戏根目录>   (bash)\n"
            "  游戏根目录里应当能看到 Modules\\ 与 Modules\\Native\\AssetPackages\\skeletons.tpac")
    return None


def find_mbtool(required: bool = True) -> Path | None:
    """定位 mbtool（.tpac 工具集，https://github.com/tridkx/bannerlord-tpac-toolkit ）。"""
    p = _env_path(_TOOLS_ENV)
    if p:
        exe = p / _MBTOOL_REL
        if exe.is_file():
            return exe
    cands = [ROOT / "mbtool", ROOT.parent / "mb-tools", ROOT.parent / "mbtool"]
    for root in _drive_roots():
        cands += [root / "mb-tools", root / "mbtool"]
    for c in cands:
        exe = c / _MBTOOL_REL
        if exe.is_file():
            return exe
    w = shutil.which("mbtool") or shutil.which("mbtool.exe")
    if w:
        return Path(w)
    if required:
        raise SystemExit(
            "★ 找不到 mbtool.exe。请克隆 https://github.com/tridkx/bannerlord-tpac-toolkit "
            "并 dotnet build，然后设置：\n"
            "    set MB_TOOLS_DIR=<仓库根目录>\n"
            "  期望存在 <仓库根>/mbtool/bin/Release/net9.0/mbtool.exe")
    return None


def find_mb_py(required: bool = True) -> Path | None:
    """mbtool 仓库里的 py/ 目录（BC 编解码等）。"""
    for f in (find_mbtool(required=False),):
        if f:
            py = f.parents[4] / "py"
            if py.is_dir():
                return py
    p = _env_path(_TOOLS_ENV)
    if p and (p / "py").is_dir():
        return p / "py"
    if required:
        raise SystemExit("★ 找不到 mbtool 仓库的 py/ 目录（设 MB_TOOLS_DIR 指向仓库根）")
    return None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("游戏目录 :", find_game(required=False))
    print("mbtool   :", find_mbtool(required=False))
    print("仓库 py/ :", find_mb_py(required=False))
