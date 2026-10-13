"""psk_lib.py —— ActorX .psk 的读写 / 子集裁剪（保留骨骼、权重、UV、顶点色）。

设计要点：
  * chunk 按原顺序原样保留，只替换被裁剪影响到的块；
  * 删面时同步删掉不再被引用的 wedge 与 point，并重映射
    FACE 的 wedge 索引、VTXW 的 point 索引、RAWWEIGHTS 的 point 索引，
    VERTEXCOLOR / EXTRAUVS* 按 wedge 索引同步裁剪，因此文件依然是合法的 PSK。
"""
import struct

import numpy as np

HDR = 32

WEDGE_DT = np.dtype([("pt", "<u4"), ("u", "<f4"), ("v", "<f4"), ("mat", "u1"), ("res", "u1"),
                     ("pad", "u2")])
FACE_DT = np.dtype([("w0", "<u2"), ("w1", "<u2"), ("w2", "<u2"), ("mat", "u1"),
                    ("aux", "u1"), ("smooth", "<i4")])
WGT_DT = np.dtype([("weight", "<f4"), ("pt", "<u4"), ("bone", "<u4")])
BONE_DT = np.dtype([("name", "S64"), ("flags", "<i4"), ("children", "<i4"), ("parent", "<i4"),
                    ("quat", "<f4", (4,)), ("pos", "<f4", (3,)), ("len", "<f4"),
                    ("size", "<f4", (3,))])


def read(path):
    """读出 chunk 列表，每个 chunk: dict(cid, tf, esz, cnt, body)。"""
    d = open(path, "rb").read()
    if d[:8] != b"ACTRHEAD":
        raise ValueError("not a PSK: %s" % path)
    o, chunks = 0, []
    while o + HDR <= len(d):
        cid = d[o:o + 20].rstrip(b"\x00").decode("latin-1")
        tf, esz, cnt = struct.unpack_from("<iii", d, o + 20)
        if esz < 0 or cnt < 0 or o + HDR + esz * cnt > len(d):
            break
        chunks.append({"cid": cid, "tf": tf, "esz": esz, "cnt": cnt,
                       "body": bytearray(d[o + HDR:o + HDR + esz * cnt])})
        o += HDR + esz * cnt
    return chunks


def write(chunks, path):
    with open(path, "wb") as f:
        for c in chunks:
            f.write(c["cid"].encode("latin-1").ljust(20, b"\x00"))
            f.write(struct.pack("<iii", c["tf"], c["esz"], c["cnt"]))
            f.write(bytes(c["body"]))


def parse(chunks):
    """把 chunk 解析成 numpy 结构。"""
    out = {"chunks": chunks}
    for c in chunks:
        cid, body, cnt = c["cid"], bytes(c["body"]), c["cnt"]
        if cid == "PNTS0000":
            out["points"] = np.frombuffer(body, "<f4").reshape(-1, 3).astype(np.float64)
        elif cid.startswith("VTXW"):
            out["wedges"] = np.frombuffer(body, WEDGE_DT).copy()
        elif cid.startswith("FACE"):
            out["faces"] = np.frombuffer(body, FACE_DT).copy()
        elif cid.startswith("MATT"):
            out["materials"] = [body[i * c["esz"]:i * c["esz"] + 64].split(b"\x00")[0]
                                .decode("latin-1") for i in range(cnt)]
        elif cid.startswith("REFSKEL"):
            out["bones"] = np.frombuffer(body, BONE_DT).copy()
        elif cid.startswith("RAWWEIGHTS"):
            out["weights"] = np.frombuffer(body, WGT_DT).copy()
        elif cid.startswith("VERTEXCOLOR"):
            out["vcolor"] = np.frombuffer(body, "u1").reshape(-1, 4).copy()
        elif cid.startswith("EXTRAUVS"):
            out["extrauvs"] = out.get("extrauvs", {})
            out["extrauvs"][cid] = np.frombuffer(body, "<f4").reshape(-1, 2).copy()
    return out


def subset(chunks, keep_faces, new_points=None):
    """只保留 keep_faces（布尔数组或索引数组）里的面；返回新的 chunk 列表。

    new_points: 可选，形状与「保留后的点表」相同的替换坐标（用于变形）。
    """
    p = parse(chunks)
    faces, wedges, points = p["faces"], p["wedges"], p["points"]
    keep_faces = np.asarray(keep_faces)
    if keep_faces.dtype == bool:
        keep_faces = np.where(keep_faces)[0]
    kf = faces[keep_faces]

    used_w = np.unique(np.stack([kf["w0"], kf["w1"], kf["w2"]], 1).ravel())
    new_wedges = wedges[used_w].copy()
    used_p = np.unique(new_wedges["pt"])
    new_pts = points[used_p]
    if new_points is not None:
        new_points = np.asarray(new_points, np.float64)
        # 允许传「全量点表」（长度=原点数）或「保留后的点表」
        assert len(new_points) in (len(points), len(new_pts)), \
            f"new_points 长度 {len(new_points)} 既不是原点数 {len(points)} 也不是保留后点数 {len(new_pts)}"
        new_pts = new_points[used_p] if len(new_points) == len(points) else new_points

    wmap = np.full(len(wedges), -1, np.int64)
    wmap[used_w] = np.arange(len(used_w))
    pmap = np.full(len(points), -1, np.int64)
    pmap[used_p] = np.arange(len(used_p))

    new_wedges["pt"] = pmap[new_wedges["pt"]].astype("<u4")
    kf = kf.copy()
    for k in ("w0", "w1", "w2"):
        kf[k] = wmap[kf[k]].astype("<u2")

    stats = {"points": (len(points), len(new_pts)), "wedges": (len(wedges), len(new_wedges)),
             "faces": (len(faces), len(kf))}

    out = []
    for c in chunks:
        cid = c["cid"]
        nc = dict(c)
        if cid == "PNTS0000":
            nc["body"] = bytearray(new_pts.astype("<f4").tobytes())
            nc["cnt"] = len(new_pts)
        elif cid.startswith("VTXW"):
            nc["body"] = bytearray(new_wedges.tobytes())
            nc["cnt"] = len(new_wedges)
        elif cid.startswith("FACE"):
            nc["body"] = bytearray(kf.tobytes())
            nc["cnt"] = len(kf)
        elif cid.startswith("RAWWEIGHTS"):
            w = p["weights"]
            m = pmap[w["pt"]] >= 0
            w2 = w[m].copy()
            w2["pt"] = pmap[w2["pt"]].astype("<u4")
            nc["body"] = bytearray(w2.tobytes())
            nc["cnt"] = len(w2)
        elif cid.startswith("VERTEXCOLOR"):
            vc = p["vcolor"][used_w]
            nc["body"] = bytearray(vc.tobytes())
            nc["cnt"] = len(vc)
        elif cid.startswith("EXTRAUVS"):
            ev = p["extrauvs"][cid][used_w]
            nc["body"] = bytearray(ev.tobytes())
            nc["cnt"] = len(ev)
        out.append(nc)
    return out, stats


def check(items):
    """基本合法性检查。"""
    p = parse(items)
    f, w, pt = p["faces"], p["wedges"], p["points"]
    assert f["w0"].max() < len(w) and f["w1"].max() < len(w) and f["w2"].max() < len(w)
    assert w["pt"].max() < len(pt)
    if "weights" in p:
        assert p["weights"]["pt"].max() < len(pt)
        assert p["weights"]["bone"].max() < len(p["bones"])
    print(f"  PSK 校验通过: points={len(pt)} wedges={len(w)} faces={len(f)} "
          f"weights={len(p.get('weights', []))} bones={len(p.get('bones', []))} "
          f"mats={len(p.get('materials', []))}")
    return p
