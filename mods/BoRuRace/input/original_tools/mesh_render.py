"""极简 z-buffer 软件渲染器：按材质槽给 PSK 网格着色出图。

用法:
  python mesh_render.py <model.psk> <out_prefix> [--slots 0,5] [--views front,side,back]
"""
import argparse
import os
import struct
import sys

import numpy as np
from PIL import Image


def parse_psk(path):
    out = {}
    with open(path, "rb") as f:
        while True:
            raw = f.read(32)
            if len(raw) < 32:
                break
            cid = raw[:20].split(b"\x00")[0].decode("latin-1")
            _, size, count = struct.unpack("<iii", raw[20:32])
            body = f.read(size * count) if size * count else b""
            if cid.startswith("PNTS"):
                out["points"] = np.frombuffer(body, "<f4").reshape(-1, 3).astype(np.float64)
            elif cid.startswith("VTXW"):
                out["wedges"] = np.frombuffer(body, np.dtype(
                    [("pt", "<i4"), ("u", "<f4"), ("v", "<f4"), ("mat", "<i2"), ("res", "<i2")]))
            elif cid.startswith("FACE"):
                out["faces"] = np.frombuffer(body, np.dtype(
                    [("w0", "<u2"), ("w1", "<u2"), ("w2", "<u2"),
                     ("mat", "u1"), ("aux", "u1"), ("smooth", "<i4")]))
            elif cid.startswith("MATT"):
                out["materials"] = [body[i * size:i * size + 64].split(b"\x00")[0].decode("latin-1")
                                    for i in range(count)]
    return out


SLOT_COLORS = {
    0: (230, 180, 150),   # 身体 - 肤色
    1: (200, 60, 60),     # 嘴/牙
    2: (60, 60, 200),     # 眼球
    3: (60, 60, 200),
    4: (40, 200, 220),    # 眼镜/饰品
    5: (70, 110, 220),    # 衣服
    6: (60, 50, 40),      # 头发
}


def render(tris, tris_mat, W=560, H=800, view="front", pad=0.06, bg=(255, 255, 255)):
    """正交投影渲染。view: front/back/left/right。tris: (n,3,3) 世界坐标。"""
    p = tris.reshape(-1, 3)
    if view == "front":
        uv = np.stack([p[:, 0], p[:, 2]], axis=1)      # 沿 -Y 看
    elif view == "back":
        uv = np.stack([-p[:, 0], p[:, 2]], axis=1)
    elif view == "left":
        uv = np.stack([p[:, 1], p[:, 2]], axis=1)      # 沿 +X 看
    else:
        uv = np.stack([-p[:, 1], p[:, 2]], axis=1)
    depth = p[:, 1] if view in ("front",) else (-p[:, 1] if view == "back" else
                                                (-p[:, 0] if view == "left" else p[:, 0]))
    depth = -depth                                     # 越大越靠近相机
    uv = uv.reshape(-1, 3, 2)
    depth = depth.reshape(-1, 3)

    lo = uv.reshape(-1, 2).min(axis=0)
    hi = uv.reshape(-1, 2).max(axis=0)
    span = hi - lo
    span = span.max()
    lo = lo - (span * pad) - (span * pad)
    scale = min(W, H) / (span * (1 + 4 * pad))
    # 屏幕坐标
    sx = (uv[:, :, 0] - lo[0]) * scale + (W - span * scale) / 2
    sy = H - ((uv[:, :, 1] - lo[1]) * scale + (H - span * scale) / 2)

    img = np.zeros((H, W, 3), np.float64)
    img[:, :] = bg
    zbuf = np.full((H, W), -1e18)

    # 光照：简单 Lambert，光从相机方向偏上
    light = np.array([-0.3, 0.6, 0.75])
    light = light / np.linalg.norm(light)

    for i in range(len(uv)):
        x0, x1, x2 = sx[i]
        y0, y1, y2 = sy[i]
        d0, d1, d2 = depth[i]
        minx = max(int(np.floor(min(x0, x1, x2))), 0)
        maxx = min(int(np.ceil(max(x0, x1, x2))), W - 1)
        miny = max(int(np.floor(min(y0, y1, y2))), 0)
        maxy = min(int(np.ceil(max(y0, y1, y2))), H - 1)
        if minx > maxx or miny > maxy:
            continue
        # 面积阈值剔除过小三角形（避免昂贵计算）
        area2 = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area2) < 1e-12:
            continue
        xs = np.arange(minx, maxx + 1) + 0.5
        ys = np.arange(miny, maxy + 1) + 0.5
        gx, gy = np.meshgrid(xs, ys)
        w0 = ((x1 - gx) * (y2 - gy) - (x2 - gx) * (y1 - gy)) / area2
        w1 = ((x2 - gx) * (y0 - gy) - (x0 - gx) * (y2 - gy)) / area2
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not m.any():
            continue
        d = w0 * d0 + w1 * d1 + w2 * d2
        sub = zbuf[miny:maxy + 1, minx:maxx + 1]
        upd = m & (d > sub)
        if not upd.any():
            continue
        sub[upd] = d[upd]
        col = np.array(SLOT_COLORS.get(int(tris_mat[i]), (255, 0, 255)), np.float64)
        # 用面的法线做一点明暗，让形状可读
        n = np.cross(tris[i][1] - tris[i][0], tris[i][2] - tris[i][0])
        ln = np.linalg.norm(n)
        shade = 0.65 if ln == 0 else 0.55 + 0.45 * abs(float(np.dot(n / ln, light)))
        region = img[miny:maxy + 1, minx:maxx + 1]
        region[upd] = col * shade
    return img.clip(0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("psk")
    ap.add_argument("out_prefix")
    ap.add_argument("--slots", default=None, help="只渲染这些槽，逗号分隔")
    ap.add_argument("--views", default="front,left,back")
    ap.add_argument("--res", default="560x800")
    a = ap.parse_args()

    W, H = (int(x) for x in a.res.split("x"))
    d = parse_psk(a.psk)
    pts, wed, faces = d["points"], d["wedges"], d["faces"]
    mats = d.get("materials", [])
    keep = None if not a.slots else set(int(x) for x in a.slots.split(","))

    sel = np.arange(len(faces))
    if keep is not None:
        sel = np.where(np.isin(faces["mat"], list(keep)))[0]
    w = np.stack([wed[faces["w0"][sel]]["pt"], wed[faces["w1"][sel]]["pt"],
                  wed[faces["w2"][sel]]["pt"]], axis=1)
    tris = pts[w]
    tmat = faces["mat"][sel]

    print(f"渲染 {len(tris)} 个三角形，槽 {sorted(set(tmat.tolist()))}")
    for v in a.views.split(","):
        img = render(tris, tmat, W, H, view=v)
        p = f"{a.out_prefix}_{v}.png"
        Image.fromarray(img).save(p)
        print("  ->", p)


if __name__ == "__main__":
    main()
