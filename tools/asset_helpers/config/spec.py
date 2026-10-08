# -*- coding: utf-8 -*-
"""本工程的资产规格：材质 / 贴图 / 装备分件。

一处定义，`convert_textures.py`（贴图 -> BC）与 `build_assets.py`（mgeo + spec + 打包）共用。

管线（alpha 分布已实测，见 docs/实测记录.md）：
  * **opaque**（alpha 全 255）：皮肤 / 脸 / 眼球 -> DXT1，不声明 has_alpha，模板 `matCloth`
  * **cutout**（真镂空，alpha 有大片 0）：睫毛 75%、发饰 43%、袖口 59%、头饰 51% 的 texel
    alpha<0.15 -> DXT5 + `has_alpha` + 模板 `matAlpha`（alphaTest）。不走 alpha test 会变成
    "整片实心板"，头发边缘发白。
  * **sheer**（明暗/覆盖度语义，alpha 大多接近 1、少数偏低）：薄纱衣料。**必须把 alpha 抬底**，
    否则 alphaTest 会把整片剪掉 —— 实机症状是"同一部位一部分可见一部分不可见"（胸口、
    袖口）。抬底公式 `a' = 0.55 + a*0.45`（下游 `hunyuan-autorig-postprocess` 对同一张贴图
    的处理，见其 docs/薄纱alpha修复.md），保证最低 0.55 > alphaTest 阈值 0.27。
"""
from __future__ import annotations

# ---------------------------------------------------------------- 装备分件
# 每个角色 3 件：HeadArmor（头/发/脸/眼/睫毛必须同 mesh —— 头部槽一次只能穿一件）
#              BodyArmor（身+手+袖，含 covers_hands）
#              LegArmor （裤/腿/鞋，covers_legs 才能盖住原版脚）
# 对象用小写子串匹配（源对象名/材质名之一命中即可）。
OUTFITS = {
    "mingyu": {
        "prefix": "my",
        "item_prefix": "my",
        "display": "圣秀·明玉",
        "parts": {
            "head": ["hairbk", "hair top", "fashi", "face", "_eye", "lash"],
            "body": [" body", "coat", "pao", "xiuzi", "wandai", "hands"],
            "legs": ["pants", " leg"],
        },
        # 源材质名 -> (输出材质短名, alpha 语义)
        #   opaque  alpha 全 255 ........................ DXT1，不声明 has_alpha
        #   cutout  **真镂空**（发片/睫毛/花边），alpha 有大片 0 ... 保留 alpha，走 alphaTest
        #   sheer   **明暗/覆盖度**语义（薄纱衣料），alpha 大多接近 1、少数偏低
        #           ...... 抬底到 0.55，否则 alphaTest 会把胸口/袖口整片剪掉
        #           （实测"同一部位一部分可见一部分不可见"就是被 alphaTest 剪的）
        "materials": {
            "shengxiu mingyu eye": ("eye", "opaque"),      # alpha 中位 1.00
            "shengxiu minyu cloth": ("cloth", "sheer"),     # 中位 1.00，但 15.3% <0.15 = 薄纱
            "shengxiu minyu face": ("face", "opaque"),
            "shengxiu minyu fashi": ("fashi", "cutout"),   # 43% 为 0 = 花边镂空
            "shengxiu minyu hair01": ("hair", "cutout"),   # 30.9% <0.15 = 发片
            "shengxiu minyu hand": ("skin", "opaque"),
            "shengxiu minyu lash": ("lash", "cutout"),     # 75.3% <0.15 = 睫毛
            "shengxiu minyu pants": ("pants", "sheer"),    # 12.4% <0.15
            "shengxiu minyu wan": ("wan", "sheer"),        # 5.0% <0.15
        },
        "armor": {"head": 22, "body": 40, "legs": 24},
        # ★ 骨集合限制：把该对象里"不在允许集合"的权重按到允许骨的距离重新分配。
        #   实测混元把**大袖子 35% 的权重给了 Spine2**（手臂只占 8%）——
        #   静止时看着没问题（袖子垂着），一抬手躯干不动、手臂被搬走 15~26 cm，
        #   袖子就被撕成碎片（离线动画 `equip_sword` f20 可见）。
        "bone_clamp": {
            "xiuzi": {14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27},
            "wandai": {15, 17, 18, 19, 20, 22, 24, 25, 26, 27},
        },
    },
    "tianxiang": {
        "prefix": "tx",
        "item_prefix": "tx",
        "display": "天香T5成女校服",
        "parts": {
            "head": ["hair", "head", "face", "_eye", "eyelash"],
            "body": ["tunic", "body", "cuff"],
            "legs": ["pants"],
        },
        "materials": {
            "M_tunic_D-PVE": ("tunic", "sheer"),      # 13.6% <0.15 = 广袖薄纱
            "M_tunic_D-PVE.001": ("tunic", "sheer"),
            "M_hair_D": ("hair", "cutout"),           # 29.4% <0.15
            "M_hair_D.001": ("hair", "cutout"),
            "M_body_D": ("skin", "opaque"),
            "M_body_D.001": ("skin", "opaque"),
            "M_body_D.002": ("skin", "opaque"),
            "M_pants_D-PVE": ("pants", "sheer"),      # 1.6% <0.15
            "M_cuff_D": ("cuff", "cutout"),           # 59.2% 为 0 = 袖口镂空
            "M_head_D": ("head", "cutout"),           # 50.8% <0.15 = 头饰
            "M_head_D.001": ("head", "cutout"),
            "M_face_D": ("face", "opaque"),
            "M_eye_D": ("eye", "opaque"),
            "M_eyelash_D": ("lash", "cutout"),
        },
        "armor": {"head": 20, "body": 38, "legs": 22},
        "bone_clamp": {
            "tunic": {9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27},
            "cuff": {15, 17, 18, 19, 20, 22, 24, 25, 26, 27},
        },
    },
}

# 材质模板（从 Native 的 materials.tpac 克隆）
TEMPLATES = {
    "matCloth": ("AssetPackages/materials.tpac", "cloak_short"),
    "matAlpha": ("AssetPackages/materials.tpac", "battania_dress_c_alpha_mat"),
}
# 网格模板 / 贴图模板
MESH_TEMPLATE = ("EmAssetPackages/armor555/armor555.tpac", "empire_legion_a")
TEX_TEMPLATE = ("EmAssetPackages/Assets.tpac", "sturgia_light_armor_c")

MAX_TEX = 2048

# This standalone preview is rebuilt exclusively from the copied Tianxiang FBX.
OUTFITS = {"tianxiang": OUTFITS["tianxiang"]}
OUTFITS["tianxiang"]["prefix"] = "gpttx"
OUTFITS["tianxiang"]["item_prefix"] = "gpttx"
# Tunic contains both sleeves and skirt: a global arm-only restriction would
# damage the skirt. Keep its existing weights pending targeted pose validation.
OUTFITS["tianxiang"]["bone_clamp"] = {}
