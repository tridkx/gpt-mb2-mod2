# -*- coding: utf-8 -*-
"""几何导出 + 资产打包。

    python pipeline/build_assets.py mingyu

产物：
    build/<tag>/mesh/<mesh>__<组号>__<材质>.mgeo
    build/<tag>/spec.json
    build/<tag>/pack0.tpac
    build/<tag>/assets.json      本包资产与 GUID 清单（跨 mod 冲突检查用）

.mgeo 布局（与 mbtool 约定一致）：
    <iii MAGIC=0x4F45474D, n_verts, n_indices>
    positions f4(n,3) | normals f4(n,3) | tangents f4(n,4) w=手性 | uv f4(n,2)
    uv2 f4(n,2) 全 0  | colors u8(n,4) **全 255** | bone_idx u8(n,4) | bone_w u8(n,4)
    indices u4(m,)

★★ 三条踩过的坑（skill §5 / §7）：
  1. **权重必须真的量化成 u8 0..255**。上游是 0..1 的 float，
     `np.asarray(w, np.uint8)` 是截断 —— 只有恰好 1.0 的变 1，其余全 0，
     于是绝大多数顶点权重全零，引擎只能让整块跟骨盆（实机"整个模型像刚体一起摇晃"）。
     这里显式 `floor(v*255)` + 余数补给最大项，并断言**每行和恰好 255**。
  2. **每个材质组必须有唯一文件名**。一个 metamesh 里同一材质常有多组，
     用 `<mesh>__<材质>.mgeo` 会同名互相覆盖（实机"同材质的袖子在、上衣不在"）。
     这里文件名带组序号。
  3. **顶点色必须写全白**：引擎用顶点色调制 albedo，写 0 会让整块变黑。
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "config"))
from paths import find_game, find_mbtool  # noqa: E402
from spec import OUTFITS, TEMPLATES, MESH_TEMPLATE, TEX_TEMPLATE  # noqa: E402

GAME = find_game()
MBTOOL = find_mbtool()
NATIVE = GAME / "Modules" / "Native"
MAGIC = 0x4F45474D

MODULE_NAME = "GptTianxiangPreview"


def quantize(vv, bb, ww, n_verts, nbones=28, k=4):
    """稀疏权重 -> 每顶点 k 槽 u8，**每行和恰为 255**。"""
    W = np.zeros((n_verts, nbones), np.float64)
    np.add.at(W, (vv, bb), ww)
    s = W.sum(1)
    orphan = np.where(s < 1e-6)[0]
    if len(orphan):
        W[orphan, 0] = 1.0                      # 兜底：跟骨盆（不能留全零，否则整块脱骨架）
    idx = np.argsort(-W, axis=1)[:, :k]
    val = np.take_along_axis(W, idx, 1)
    val = val / np.maximum(val.sum(1, keepdims=True), 1e-12)
    q = np.floor(val * 255.0).astype(np.int32)
    rest = 255 - q.sum(1)
    q[np.arange(n_verts), np.argmax(val, 1)] += rest
    assert (q >= 0).all(), "量化出现负值"
    ss = q.sum(1)
    assert (ss == 255).all(), f"权重和 != 255 的顶点有 {(ss != 255).sum()} 个"
    assert idx.max() <= 27, "骨索引越界"
    return idx.astype(np.uint8), q.astype(np.uint8), len(orphan)


def vertex_tangents(P, tris, uv, nrm):
    """按 UV 重算切线（源约定可能与引擎不同，重算最稳），退化处取任意垂直方向。"""
    n = len(P)
    tan = np.zeros((n, 3))
    bit = np.zeros((n, 3))
    v0, v1, v2 = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    t0, t1, t2 = uv[tris[:, 0]], uv[tris[:, 1]], uv[tris[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    d1, d2 = t1 - t0, t2 - t0
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    ok = np.abs(det) > 1e-12
    r = np.zeros_like(det)
    r[ok] = 1.0 / det[ok]
    T = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * r[:, None]
    B = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) * r[:, None]
    for i in range(3):
        np.add.at(tan, tris[:, i], T)
        np.add.at(bit, tris[:, i], B)
    tan = tan - nrm * np.sum(nrm * tan, 1, keepdims=True)
    ln = np.linalg.norm(tan, axis=1, keepdims=True)
    bad = ln[:, 0] < 1e-9
    if bad.any():
        tmp = np.tile(np.array([1.0, 0.0, 0.0]), (n, 1))
        tmp[np.abs(nrm[:, 0]) > 0.9] = np.array([0.0, 1.0, 0.0])
        alt = np.cross(nrm, tmp)
        alt /= np.maximum(np.linalg.norm(alt, axis=1, keepdims=True), 1e-12)
        tan[bad] = alt[bad]
    tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    # 手性写进 w：与法线/切线的叉积对齐 bitangent
    w = np.where(np.sum(np.cross(nrm, tan) * bit, 1) < 0, -1.0, 1.0)
    return np.concatenate([tan, w[:, None]], 1).astype(np.float32)


def write_mgeo(path, P, N, T, UV, BI, BW, tris):
    n, m = len(P), tris.size
    with open(path, "wb") as f:
        f.write(np.array([MAGIC, n, m], "<i4").tobytes())
        f.write(np.asarray(P, "<f4").tobytes())
        f.write(np.asarray(N, "<f4").tobytes())
        f.write(np.asarray(T, "<f4").tobytes())
        f.write(np.asarray(UV, "<f4").tobytes())
        f.write(np.zeros((n, 2), "<f4").tobytes())
        f.write(np.full((n, 4), 255, np.uint8).tobytes())
        f.write(np.asarray(BI, np.uint8).tobytes())
        f.write(np.asarray(BW, np.uint8).tobytes())
        f.write(np.asarray(tris, "<u4").tobytes())


def derive_guid(seed):
    """★ 包 GUID 必须随工程变化 —— 写死常量会让所有用同一工具构建的 mod 撞车。"""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"bannerlord-mod/{seed}/pack0"))


def main():
    """一次打包**所有**角色到同一个 pack0.tpac。

    ★ 为什么要合并成一个包：离线预览器 `baker/bake.py` 是
      `MB.exportmod(packs[0], ...)` —— **只导出第一个 tpac**。
      分成 mingyu.tpac + tianxiang.tpac 时，天香在预览器里是
      "0 绘制 / 0 三角 ⚠ 无可见网格"（items 读到了，网格没加载）。
      游戏本身会加载 AssetPackages/ 下全部 tpac，所以那只是预览器的限制，
      但既然合并成单包没有任何代价，就合并。
    """
    tags = sys.argv[1:] or list(OUTFITS)
    build = ROOT / "build"
    (build / "mesh").mkdir(parents=True, exist_ok=True)
    for f in (build / "mesh").glob("*.mgeo"):
        f.unlink()

    spec = {
        "output": str(build / "pack0.tpac"),
        "packageGuid": derive_guid(MODULE_NAME),
        "templates": {
            "mesh": {"tpac": str(NATIVE / MESH_TEMPLATE[0]), "name": MESH_TEMPLATE[1]},
            "texBC1": {"tpac": str(NATIVE / TEX_TEMPLATE[0]), "name": TEX_TEMPLATE[1]},
            "texDXT5": {"tpac": str(NATIVE / TEX_TEMPLATE[0]), "name": TEX_TEMPLATE[1]},
        },
        "textures": [], "materials": [], "meshes": [],
    }
    for k, (tp, nm) in TEMPLATES.items():
        spec["templates"][k] = {"tpac": str(NATIVE / tp), "name": nm}

    tex_seen, mat_mode, matname_to_mode, groups = set(), {}, {}, []
    for tag in tags:
        cfg = OUTFITS[tag]
        z = np.load(ROOT / "work" / f"{tag}_chain.npz")
        meta = json.load(open(ROOT / "work" / f"{tag}_chain.json", encoding="utf-8"))
        texman = json.loads((ROOT / "build" / tag / "tex_manifest.json").read_text(encoding="utf-8"))

        P = z["verts"].astype(np.float64)
        N = z["normals"].astype(np.float64)
        UV = z["uvs"].astype(np.float64).copy()
        # ★ 翻 V：Blender 的 UV 是 bottom-origin（v=0 在贴图**底**行），而引擎/.bc 是
        #   top-origin（v=0 在**顶**行，PNG 行序即顶行在前）。
        #   不翻 = 五官上下颠倒。★ 必须在**算切线之前**翻，否则切线手性跟着错
        #   （症状是"颜色错位 + 法线假褶皱"）。
        UV[:, 1] = 1.0 - UV[:, 1]
        F = z["tris"].astype(np.int64)
        BI, BW, n_orph = quantize(z["w_vidx"], z["w_bidx"], z["w_w"], len(P))
        print(f"\n[{tag}] 权重量化：{len(P)} 顶点，兜底 {n_orph}；每行和==255 ✓；索引 max={BI.max()}")

        parts = cfg["parts"]
        tri_part = np.full(len(F), "", dtype=object)
        tri_mat = np.full(len(F), "", dtype=object)
        for o in meta["objects"]:
            key = (o["name"] + " " + " ".join(o["materials"])).lower()
            part = next((p for p, kws in parts.items() if any(k in key for k in kws)), None)
            if part is None:
                raise SystemExit(f"{tag}: 对象 {o['name']} 没有匹配到 part")
            src_mat = o["materials"][0]
            if src_mat not in cfg["materials"]:
                raise SystemExit(f"{tag}: 材质 {src_mat} 不在 config/spec.py")
            sl = slice(o["t_off"], o["t_off"] + o["tris"])
            tri_part[sl] = part
            out_mat = f"{cfg['prefix']}_{cfg['materials'][src_mat][0]}"
            tri_mat[sl] = out_mat
            matname_to_mode[out_mat] = cfg["materials"][src_mat][1]

        for pname in parts:
            mesh_name = f"{cfg['prefix']}_{pname}"
            for gi, matname in enumerate(sorted(set(tri_mat[tri_part == pname]))):
                sel = (tri_part == pname) & (tri_mat == matname)
                tri = F[sel]
                if not len(tri):
                    continue
                vids = np.unique(tri)
                remap = np.full(len(P), -1, np.int64)
                remap[vids] = np.arange(len(vids))
                t = remap[tri].astype(np.uint32)
                T = vertex_tangents(P[vids], t.astype(np.int64), UV[vids], N[vids])
                fn = f"{mesh_name}__{gi:02d}__{matname}.mgeo"
                write_mgeo(build / "mesh" / fn, P[vids], N[vids], T, UV[vids],
                           BI[vids], BW[vids], t)
                groups.append({"mesh": mesh_name, "geometry": str(build / "mesh" / fn),
                               "material": matname, "name": f"{mesh_name}.{gi}",
                               "flags": [], "materialFlags": [],
                               "tris": int(len(t)), "verts": int(len(vids))})
                print(f"  {fn:<46} 面={len(t):<6} 顶点={len(vids)}")

        for name, t in sorted(texman.items()):
            if name in tex_seen:
                continue
            tex_seen.add(name)
            spec["textures"].append({
                "name": name,
                "template": "texDXT5" if t["format"] == "DXT5" else "texBC1",
                "blob": t["file"], "width": t["width"], "height": t["height"],
                "mips": t["mips"], "format": t["format"], "flags": [],
                "systemFlags": ["has_alpha"] if t["has_alpha"] else [],
            })

    used_mats = sorted({g["material"] for g in groups})
    for matname in used_mats:
        mode = matname_to_mode.get(matname, "opaque")
        # ★ 槽位 1/2 显式指向本角色的**平坦法线**：不写就会继承模板（原版裙子）的
        #   法线/细节法线，实测表现为"花纹错位 + 假褶皱"（lumine 工程踩过同一个坑）。
        flat = f"{matname.split('_')[0]}_flat_n"
        spec["materials"].append({
            "name": matname, "mode": mode,
            "template": "matCloth" if mode == "opaque" else "matAlpha",
            "textures": {"0": f"{matname}_d", "1": flat, "2": flat},
        })
        print(f"  材质 {matname:<14} mode={mode:<7} -> {spec['materials'][-1]['template']}")
    for mesh_name in sorted({g["mesh"] for g in groups}):
        gs = [{"geometry": g["geometry"], "material": g["material"], "name": g["name"],
               "flags": [], "materialFlags": []} for g in groups if g["mesh"] == mesh_name]
        spec["meshes"].append({"name": mesh_name, "bodyPart": "", "template": "mesh",
                               "groups": gs})
    (build / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    (build / "assets.json").write_text(json.dumps(
        {"packageGuid": spec["packageGuid"], "meshes": [m["name"] for m in spec["meshes"]],
         "materials": used_mats, "textures": sorted(tex_seen)}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nspec: {len(spec['meshes'])} 网格 / {len(spec['materials'])} 材质 / "
          f"{len(spec['textures'])} 贴图；包 GUID {spec['packageGuid']}")

    r = subprocess.run([str(MBTOOL), "build", str(build / "spec.json")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout or ""
    print(out[-2500:])
    if r.returncode != 0 or "error" in (r.stderr or "").lower() or "error" in out.lower():
        print("STDERR:", (r.stderr or "")[-2000:])
        raise SystemExit("打包失败")
    print("打包完成:", build / "pack0.tpac")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
