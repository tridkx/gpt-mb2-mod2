"""按高度切除身体槽的脚部几何，输出新的 PSK（骨骼/权重/UV/其他槽都不动）。

用法:
  python feet_cut.py <in.psk> <out.psk> --z-cut 17.4 [--slot 0]
  python feet_cut.py <in.psk> <out.psk> --probe        # 只诊断，不写文件
"""
import argparse
import os
import sys

import numpy as np

import psk_lib


def shoe_top(parsed, cloth_slot=5, zmax=25):
    """找「鞋」的高度上限：槽 5 里整体都在脚部高度的连通分量。"""
    faces, wedges, pts = parsed["faces"], parsed["wedges"], parsed["points"]
    sel = np.where(faces["mat"] == cloth_slot)[0]
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in sel:
        w = [int(wedges[faces[k][i]]["pt"]) for k in ("w0", "w1", "w2")]
        a, b, c = (find(x) for x in w)
        parent[b] = a
        parent[c] = a
    groups = {}
    for i in sel:
        w = [int(wedges[faces[k][i]]["pt"]) for k in ("w0", "w1", "w2")]
        groups.setdefault(find(w[0]), []).append(i)
    tops = []
    for g in groups.values():
        gi = np.array(g)
        w = np.stack([wedges[faces["w0"][gi]]["pt"], wedges[faces["w1"][gi]]["pt"],
                      wedges[faces["w2"][gi]]["pt"]], 1)
        p = pts[np.unique(w)]
        if p[:, 2].max() < zmax:
            tops.append((p[:, 2].max(), len(gi)))
    return tops


def cut(inp, outp, z_cut, slot=0, probe=False):
    chunks = psk_lib.read(inp)
    p = psk_lib.parse(chunks)
    faces, wedges, pts = p["faces"], p["wedges"], p["points"]

    # 每个面的平均高度（用质心判定，切口不会留下跨越空隙）
    z0 = pts[wedges[faces["w0"]]["pt"]][:, 2]
    z1 = pts[wedges[faces["w1"]]["pt"]][:, 2]
    z2 = pts[wedges[faces["w2"]]["pt"]][:, 2]
    fz = (z0 + z1 + z2) / 3.0
    is_body = faces["mat"] == slot
    kill = is_body & (fz < z_cut)
    print(f"身体槽面数 {int(is_body.sum())}，其中最低点 < {z_cut} 的面 {int(kill.sum())} "
          f"({kill.sum()/max(is_body.sum(),1)*100:.1f}%)")
    keep = ~kill

    # 切面附近的顶点统计
    kill_w = np.unique(np.stack([faces["w0"][kill], faces["w1"][kill],
                                 faces["w2"][kill]], 1).ravel()) if kill.any() else np.array([], int)
    keep_w = np.unique(np.stack([faces["w0"][keep], faces["w1"][keep],
                                 faces["w2"][keep]], 1).ravel())
    print(f"  受影响 wedge: 删除 {len(kill_w)}，保留 {len(keep_w)}，"
          f"两者共用 {len(np.intersect1d(kill_w, keep_w))}")

    if probe:
        return

    # 把保留下来的身体顶点里低于切口的一律抬到切口平面：
    # 切口变得平齐、不再有下垂的锯齿尖刺。
    pts2 = pts.copy()
    keep_w_body = np.unique(np.stack([faces["w0"][keep & is_body], faces["w1"][keep & is_body],
                                      faces["w2"][keep & is_body]], 1).ravel())
    keep_p_body = np.unique(wedges[keep_w_body]["pt"])      # wedge 索引 -> point 索引
    low = keep_p_body[pts[keep_p_body][:, 2] < z_cut]
    pts2[low, 2] = z_cut
    print(f"  切口整平：抬高 {len(low)} 个顶点到 Z={z_cut}")

    out_chunks, stats = psk_lib.subset(chunks, keep, new_points=pts2)
    print(f"  点 {stats['points'][0]} -> {stats['points'][1]}，"
          f"楔 {stats['wedges'][0]} -> {stats['wedges'][1]}，"
          f"面 {stats['faces'][0]} -> {stats['faces'][1]}")
    psk_lib.write(out_chunks, outp)
    print("  写出", outp, os.path.getsize(outp), "字节")
    p2 = psk_lib.check(out_chunks)
    # 剩余身体的最低点
    f2, w2, pt2 = p2["faces"], p2["wedges"], p2["points"]
    bm = f2["mat"] == slot
    bpts = pt2[np.unique(np.stack([w2[f2["w0"][bm]]["pt"], w2[f2["w1"][bm]]["pt"],
                                   w2[f2["w2"][bm]]["pt"]], 1).ravel())]
    print(f"  裁剪后身体最低点 Z = {bpts[:,2].min():.2f}（切口高度 {z_cut}）")
    return p2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--z-cut", type=float, default=None)
    ap.add_argument("--slot", type=int, default=0)
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()

    parsed = psk_lib.parse(psk_lib.read(a.inp))
    tops = shoe_top(parsed)
    print("鞋分量（整体低于 25 的槽 5 连通块）顶高：",
          ", ".join(f"{t:.2f}({n}面)" for t, n in sorted(tops)))
    # 默认：取面数最多的那个鞋分量（= 鞋帮外壳）的顶高，再往下让 0.3
    main_top = max(tops, key=lambda t: t[1])[0]
    z = a.z_cut if a.z_cut is not None else round(main_top - 0.3, 2)
    print(f"使用切割高度 Z = {z:.2f}（默认 = 鞋帮外壳顶 {main_top:.2f} - 0.30）")
    cut(a.inp, a.out, z, slot=a.slot, probe=a.probe)


if __name__ == "__main__":
    main()
