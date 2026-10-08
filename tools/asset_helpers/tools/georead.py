# -*- coding: utf-8 -*-
"""读 mbtool `exportmod` 产出的 `geo/*.bin`（GDMB 格式）。

格式取自 mbtool 的**写入端源码** `mbtool/src/ExportMod.cs`：

    u32 magic('GDMB') | u32 version | u32 submeshCount
    每个子网格：
      utf8(name) | i32 lod | utf8(matName) | ascii36(materialGuid)
      u32 nVerts | u32 nIndices | 6×f32 bbox | u32 flags
      f32×3 positions   (n)
      [f32×3 normals]   if flags&1
      f32×2 uv1         (n)
      [f32×2 uv2]       if flags&2
      [u8×4 colors1]    if flags&4      ← 每顶点 **4** 字节（不是 16）
      [u8×4 colors2]    if flags&8      ← 同上
      [f32×4 tangents]  if flags&16
      [u8×4 boneIdx]    if flags&32
      u8×4 boneWeights  (n)
      [i32 indices]     (nIndices)

  `utf8` / `ascii36` 都是 **u32 长度前缀 + 字节**。

★ 为什么要自己实现：上游读取器 `import_mod.py` 属于 mb-tools 的 `preview/` 目录，
  该目录在某次整理中丢失，而 `tools/audit_skin.py` 依赖它 ⇒
  **「从最终 .tpac 倒推」这一层验证会静默失效**（verify 只看到"退出码非 0"）。
  这里按写入端源码重写，读回来即可自校验（magic/version/尺寸都要对得上）。
"""
from __future__ import annotations

import struct
from pathlib import Path

import numpy as np


def read_geo(path) -> list:
    """返回子网格列表，每项含 name/lod/material/guid/nverts/nidx/bbox/flags/bw/bi/pos/uv。"""
    d = Path(path).read_bytes()
    o = 0

    def u32():
        nonlocal o
        v = struct.unpack_from("<I", d, o)[0]
        o += 4
        return v

    def i32():
        nonlocal o
        v = struct.unpack_from("<i", d, o)[0]
        o += 4
        return v

    def blob():
        nonlocal o
        n = i32()
        v = d[o:o + n]
        o += n
        return v

    magic = u32()
    ver = u32()
    cnt = u32()
    if magic != 0x424D4447:
        raise ValueError(f"{path}: 不是 GDMB 格式（magic={magic:#x}）")
    subs = []
    for _ in range(cnt):
        name = blob().decode("utf-8", "replace")
        lod = i32()
        mat = blob().decode("utf-8", "replace")
        guid = blob().decode("ascii", "replace")
        n = u32()
        ni = u32()
        bb = struct.unpack_from("<6f", d, o)
        o += 24
        flags = u32()
        pos = np.frombuffer(d, np.float32, n * 3, o).reshape(n, 3).copy()
        o += n * 12
        if flags & 1:
            o += n * 12                      # normals
        uv = np.frombuffer(d, np.float32, n * 2, o).reshape(n, 2).copy()
        o += n * 8
        if flags & 2:
            o += n * 8                       # uv2
        if flags & 4:
            o += n * 4                       # colors1（R,G,B,A 各 1 u8）
        if flags & 8:
            o += n * 4                       # colors2
        if flags & 16:
            o += n * 16                      # tangents
        bi = None
        if flags & 32:
            bi = np.frombuffer(d, np.uint8, n * 4, o).reshape(n, 4).copy()
            o += n * 4
        bw = np.frombuffer(d, np.uint8, n * 4, o).reshape(n, 4).copy()
        o += n * 4
        idx = None
        if ni > 0:
            idx = np.frombuffer(d, np.int32, ni, o).copy()
            o += ni * 4
        subs.append({"name": name, "lod": lod, "material": mat, "guid": guid,
                     "nverts": n, "nidx": ni, "bbox": bb, "flags": flags,
                     "pos": pos, "uv": uv, "bw": bw, "bi": bi, "idx": idx})
    return subs


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for p in sys.argv[1:]:
        for s in read_geo(p):
            print(f"  {s['name']:<24} v={s['nverts']:<6} i={s['nidx']:<7} mat={s['material']:<12} "
                  f"bi={'有' if s['bi'] is not None else '无'}")
