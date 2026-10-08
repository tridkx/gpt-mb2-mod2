# -*- coding: utf-8 -*-
"""贴图 -> BC（BC1/BC3）+ 完整 mip 链。

    python pipeline/convert_textures.py mingyu
    python pipeline/convert_textures.py tianxiang

输入：`work/<tag>_raw.json` 里的 textures（extract.py 按 `<材质名>__<槽位>` 导出）
输出：`build/<tag>/tex/<out>_d.bc`、`build/<tag>/tex_png/*.png`、`build/<tag>/tex_manifest.json`

★ `.bc` 必须带**完整 mip 链**，否则打包器报 `blob too small for mip 1`。
★ `has_alpha` 是**资产标志**不是"字节里有没有 alpha"：镂空材质漏了它，
  材质侧的 alphaTest 怎么调都不生效（表现是黑片/白片）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "config"))
from paths import find_mb_py  # noqa: E402
sys.path.insert(0, str(find_mb_py()))
from bcencode import encode_bc1, encode_bc3, encode_bc5, full_mip_count  # noqa: E402

from spec import OUTFITS, MAX_TEX  # noqa: E402


def downsample(a):
    """2x2 盒式降采样 —— 交给 PIL 处理奇偶/1 像素边界。全程 uint8（编码器只吃 uint8）。"""
    h, w = a.shape[:2]
    mode = "RGBA" if a.shape[2] == 4 else "RGB"
    return np.asarray(Image.fromarray(a, mode).resize(
        (max(1, w // 2), max(1, h // 2)), Image.BOX), np.uint8)


def encode_mips(rgba, fmt):
    cur, parts, mips = rgba, [], 0
    while True:
        if fmt == "BC5":
            parts.append(encode_bc5(np.ascontiguousarray(cur[:, :, :2])))
        elif fmt == "DXT5":
            parts.append(encode_bc3(cur))
        else:
            parts.append(encode_bc1(cur))
        mips += 1
        h, w = cur.shape[:2]
        if w == 1 and h == 1:
            break
        cur = downsample(cur)
    return b"".join(parts), mips


def resize_cap(a, cap):
    h, w = a.shape[:2]
    m = max(h, w)
    if m <= cap:
        return a, w, h
    s = cap / m
    nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
    mode = "RGBA" if a.shape[2] == 4 else "RGB"
    return np.asarray(Image.fromarray(a, mode).resize((nw, nh), Image.LANCZOS), np.uint8), nw, nh


def main():
    tag = sys.argv[1]
    cfg = OUTFITS[tag]
    meta = json.load(open(ROOT / "work" / f"{tag}_raw.json", encoding="utf-8"))
    tex = meta["textures"]          # key = "<材质名>__<槽位>"

    out_tex = ROOT / "build" / tag / "tex"
    out_png = ROOT / "build" / tag / "tex_png"
    out_tex.mkdir(parents=True, exist_ok=True)
    out_png.mkdir(parents=True, exist_ok=True)
    for d in (out_tex, out_png):                 # 幂等：清空，否则旧 .bc 会被打进去
        for f in d.glob("*"):
            f.unlink()

    # 输出贴图名 -> (源材质名, alpha 语义 opaque/cutout/sheer)
    plan = {}
    for src_mat, (short, mode) in cfg["materials"].items():
        name = f"{cfg['prefix']}_{short}_d"
        if name in plan:
            continue
        plan[name] = (src_mat, mode)

    man = {}
    total = 0
    # ---- 平坦法线（共享一张）
    # ★ 材质是从 Native 的 `battania_dress_c_alpha_mat` / `cloak_short` 克隆的，
    #   **槽位 1/2/4 仍指向原版裙子自己的贴图**（GUID 不同但引用的是原版资产）。
    #   实测 dump：槽 0 换成本工程的 albedo 后，[1] [2] [4] 与模板一字不差 ——
    #   不显式指定就会渲染出"原版裙子的花纹/法线"，表现为贴图错位 + 假褶皱。
    #   没有源法线可用时（两个模型大部分材质都没有 `_n`），统一用 128² 平坦法线。
    flat_name = f"{cfg['prefix']}_flat_n"
    a = np.zeros((128, 128, 4), np.uint8)
    a[:, :, 0] = a[:, :, 1] = 128
    a[:, :, 2] = 255
    a[:, :, 3] = 255
    blob, mips = encode_mips(a, "BC5")
    (out_tex / f"{flat_name}.bc").write_bytes(blob)
    Image.fromarray(a, "RGBA").save(out_png / f"{flat_name}.png")
    man[flat_name] = {"file": str(out_tex / f"{flat_name}.bc"), "width": 128, "height": 128,
                      "mips": mips, "format": "BC5", "has_alpha": False,
                      "source": "(generated flat normal)", "bytes": len(blob)}
    total += len(blob)
    print(f"  {flat_name:<18}  128x128  BC5    平坦法线（中性化槽位 1/2）")

    for name, (src_mat, mode) in sorted(plan.items()):
        is_alpha = mode != "opaque"
        # ★ extract.py 把材质名里的空格换成了下划线（"shengxiu minyu cloth" ->
        #   "shengxiu_minyu_cloth"），查表要按同一套 sanitize 规则
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in src_mat)
        rec = tex.get(f"{safe}__d")
        if not rec or not rec.get("saved"):
            raise SystemExit(f"缺贴图：{src_mat}__d")
        a = np.asarray(Image.open(rec["saved"]).convert("RGBA"), np.uint8)
        a, w, h = resize_cap(a, MAX_TEX)
        fmt = "DXT5" if is_alpha else "DXT1"
        if not is_alpha:
            a = a.copy()
            a[:, :, 3] = 255          # BC1 无 alpha；让预览与"编码后实际表现"一致
        elif mode == "sheer":
            # ★ 明暗/覆盖度语义：把 alpha 抬底到 0.55，否则 alphaTest 会整片剪掉
            #   （实机症状：胸口、袖口"同一部位一部分可见一部分不可见"）。
            #   公式与 hunyuan-autorig-postprocess 对同一张贴图的处理一致。
            al = a[:, :, 3].astype(np.float32) / 255.0
            a = a.copy()
            a[:, :, 3] = np.clip(0.55 + al * 0.45, 0, 1).__mul__(255).astype(np.uint8)
        # cutout：保留原 alpha（镂空必须真的镂掉）
        blob, mips = encode_mips(a, fmt)
        (out_tex / f"{name}.bc").write_bytes(blob)
        Image.fromarray(a, "RGBA").save(out_png / f"{name}.png")
        man[name] = {"file": str(out_tex / f"{name}.bc"), "width": w, "height": h,
                     "mips": mips, "format": fmt, "has_alpha": bool(is_alpha),
                     "source": src_mat, "bytes": len(blob)}
        total += len(blob)
        al = a[:, :, 3].astype(np.float32) / 255
        print(f"  {name:<18} {w:>4}x{h:<4} {fmt:<5} {mode:<6} mips={mips:<3} {len(blob)/1024:7.1f} KB "
              f" has_alpha={is_alpha}  A[min {al.min():.2f} med {np.median(al):.2f} "
              f"zero {(al<0.02).mean()*100:4.1f}%]")
        if mips != full_mip_count(w, h):
            raise SystemExit(f"{name}: mip 数 {mips} != {full_mip_count(w,h)}")

    (ROOT / "build" / tag / "tex_manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"合计 {total/1024/1024:.2f} MB -> build/{tag}/tex_manifest.json")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()