"""穿模诊断：把「身体」和「鞋」分开着色渲染，并量化脚有多少落在鞋外。

用法: python feet_check.py <model.psk> <out_prefix>
"""
import sys

import numpy as np
from PIL import Image

from mesh_render import parse_psk


def tri_of(pts, wed, faces, sel):
    w = np.stack([wed[faces["w0"][sel]]["pt"], wed[faces["w1"][sel]]["pt"],
                  wed[faces["w2"][sel]]["pt"]], 1)
    return pts[w], w


def components_pts(faces, wed, pts, mat):
    sel = np.where(faces["mat"] == mat)[0]
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in sel:
        w = [int(wed[faces[k][i]]["pt"]) for k in ("w0", "w1", "w2")]
        a, b, c = (find(x) for x in w)
        parent[b] = a
        parent[c] = a
    groups = {}
    for i in sel:
        w = [int(wed[faces[k][i]]["pt"]) for k in ("w0", "w1", "w2")]
        r = find(w[0])
        g = groups.setdefault(r, {"pts": set(), "faces": []})
        g["pts"].update(w)
        g["faces"].append(i)
    return groups


def render_layers(layers, out, W=680, H=820, view="front", zcrop=None, pad=0.08):
    """layers: [(tris, rgb)]，按顺序画，共用 z-buffer。"""
    allp = np.concatenate([t.reshape(-1, 3) for t, _ in layers], 0)
    if zcrop is not None:
        allp = allp[allp[:, 2] <= zcrop]
    if view == "front":
        uv = np.stack([allp[:, 0], allp[:, 2]], 1)
    elif view == "back":
        uv = np.stack([-allp[:, 0], allp[:, 2]], 1)
    elif view == "top":
        uv = np.stack([allp[:, 0], allp[:, 1]], 1)
    else:
        uv = np.stack([allp[:, 1], allp[:, 2]], 1)
    lo, hi = uv.min(0), uv.max(0)
    span = (hi - lo).max()
    lo = lo - span * pad
    scale = min(W, H) / (span * (1 + 2 * pad))
    img = np.full((H, W, 3), 255.0)
    zbuf = np.full((H, W), -1e18)

    def draw(tris, color):
        p = tris.reshape(-1, 3)
        if view == "front":
            u = np.stack([p[:, 0], p[:, 2]], 1); dep = -p[:, 1]
        elif view == "back":
            u = np.stack([-p[:, 0], p[:, 2]], 1); dep = p[:, 1]
        elif view == "top":
            u = np.stack([p[:, 0], p[:, 1]], 1); dep = p[:, 2]
        else:
            u = np.stack([p[:, 1], p[:, 2]], 1); dep = -p[:, 0]
        u = u.reshape(-1, 3, 2); dep = dep.reshape(-1, 3)
        sx = (u[:, :, 0] - lo[0]) * scale + (W - span * scale) / 2
        sy = H - ((u[:, :, 1] - lo[1]) * scale + (H - span * scale) / 2)
        for i in range(len(sx)):
            x0, x1, x2 = sx[i]; y0, y1, y2 = sy[i]
            d0, d1, d2 = dep[i]
            minx = max(int(np.floor(min(x0, x1, x2))), 0)
            maxx = min(int(np.ceil(max(x0, x1, x2))), W - 1)
            miny = max(int(np.floor(min(y0, y1, y2))), 0)
            maxy = min(int(np.ceil(max(y0, y1, y2))), H - 1)
            if minx > maxx or miny > maxy:
                continue
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
            n = np.cross(tris[i][1] - tris[i][0], tris[i][2] - tris[i][0])
            ln = np.linalg.norm(n)
            sh = 0.7 if ln == 0 else 0.6 + 0.4 * abs(float(n[2] / ln))
            img[miny:maxy + 1, minx:maxx + 1][upd] = np.array(color) * sh
    for tris, color in layers:
        if zcrop is not None:
            keep = tris[:, :, 2].max(axis=1) <= zcrop
            tris = tris[keep]
        draw(tris, color)
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(out)
    print("->", out)


def main():
    psk, prefix = sys.argv[1], sys.argv[2]
    d = parse_psk(psk)
    pts, wed, faces = d["points"], d["wedges"], d["faces"]

    body_sel = np.where(faces["mat"] == 0)[0]
    body_tris, body_w = tri_of(pts, wed, faces, body_sel)
    groups = components_pts(faces, wed, pts, 5)
    shoes = []
    for g in groups.values():
        p = pts[np.array(sorted(g["pts"]))]
        if p[:, 2].max() < 20:                      # 鞋：整体都在脚部高度
            shoes.append(g)
    print(f"鞋分量 {len(shoes)} 个，面数 {[len(g['faces']) for g in shoes]}")
    shoe_sel = np.concatenate([np.array(g["faces"]) for g in shoes])
    shoe_tris, shoe_w = tri_of(pts, wed, faces, shoe_sel)

    # --- 身体脚顶点 vs 鞋：射线奇偶判定内外 ---
    body_pts_idx = np.unique(body_w.ravel())
    bp = pts[body_pts_idx]
    foot_mask = bp[:, 2] < 25
    P = bp[foot_mask]
    print(f"\n身体顶点总数 {len(bp)}，脚部(Z<25) {len(P)}")
    A = shoe_tris[:, 0]; B = shoe_tris[:, 1]; C = shoe_tris[:, 2]
    e1 = B - A; e2 = C - A
    # 从 +X 方向来的射线: o + t*(-1,0,0)
    dirv = np.array([1.0, 0.0, 0.0])
    pv = np.cross(dirv, e2)
    det = np.einsum("nk,nk->n", e1, pv)
    inside_cnt = np.zeros(len(P), dtype=int)
    for i, o in enumerate(P):
        good = np.abs(det) > 1e-12
        inv = np.zeros(len(det)); inv[good] = 1.0 / det[good]
        tv = o - A
        u = np.einsum("nk,nk->n", tv, pv) * inv
        qv = np.cross(tv, e1)
        v = np.einsum("k,nk->n", dirv, qv) * inv
        t = np.einsum("nk,nk->n", e2, qv) * inv
        hit = good & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        inside_cnt[i] = hit.sum()
    inside = (inside_cnt % 2) == 1
    print(f"  判定在鞋**内部** {inside.sum()}，在鞋**外部**（含小腿以上） {(~inside).sum()}")
    zz = P[~inside][:, 2]
    if len(zz):
        print(f"  鞋外顶点的 Z 分布: min={zz.min():.2f} max={zz.max():.2f} "
              f"中位={np.median(zz):.2f}")
        for lo, hi in [(0, 4), (4, 8), (8, 12), (12, 16), (16, 20), (20, 25)]:
            m = (zz >= lo) & (zz < hi)
            print(f"    Z {lo:2d}~{hi:2d}: {m.sum():4d} 个在外")
    out_foot = P[~inside & (P[:, 2] < 20)]
    print(f"  Z<20 且判定在鞋外的顶点: {len(out_foot)}")

    # 鞋顶高度
    sp = shoe_tris.reshape(-1, 3)
    print(f"\n鞋包围盒 Z {sp[:,2].min():.2f}~{sp[:,2].max():.2f}  "
          f"X {sp[:,0].min():.1f}~{sp[:,0].max():.1f}  Y {sp[:,1].min():.1f}~{sp[:,1].max():.1f}")

    render_layers([(body_tris, (232, 190, 170)), (shoe_tris, (60, 100, 220))],
                  f"{prefix}_feet_front.png", view="front", zcrop=40, W=680, H=680)
    render_layers([(body_tris, (232, 190, 170)), (shoe_tris, (60, 100, 220))],
                  f"{prefix}_feet_left.png", view="left", zcrop=40, W=680, H=680)
    render_layers([(body_tris, (232, 190, 170)), (shoe_tris, (60, 100, 220))],
                  f"{prefix}_feet_top.png", view="top", zcrop=40, W=680, H=680)


if __name__ == "__main__":
    main()
