# BoRu - Modern Outfit

孟柏汝去脚版的独立骑砍2装备模块，版本 v1.0.0。固定外观，不包含面部表情或捏脸兼容。推荐女性角色成套穿戴：发容与眼镜、白衬衫与牛仔裤、双手与腕饰、帆布鞋。四件均为商品，也可在作弊物品列表搜索“孟柏汝”。模块管理器显示名为英文 `BoRu - Modern Outfit`。

原始网格来自 `D:/dsh-nvguiqiao/repo/models/08_孟柏汝_BoRu_女_去脚/`，贴图来自相邻原版 `08_孟柏汝_BoRu_女/textures/`。input 保存独立副本、原说明、源工具和 SHA256；原目录只读使用。原版去脚切口保留，鞋口仍需游戏动作测试。

原始 ActorX 骨架有 80 骨，适配本机实际导出的 28 骨 human skeleton。原始权重合并到原生骨骼，再以统一空间场适配绑定姿态；皮肤切口按三角面精确插值，跨装备共享位置、法线和权重。脸、头发、眼睛及眼镜固定随头；手型固定随原生手掌，未制作完整手指握持形变。短发、衬衫和长裤采用蒙皮，无游戏布料求解器。

按反馈将腿部局部横截面收窄 20%、前后厚度减小 15%，腿长保留；头、头发、眼镜整体放大 12%；脚部横向收窄 15%，脚长和高度保留。修正虹膜 UV，并分离眼白与睫毛透明片，避免黑瞳铺满眼球。

四级 LOD 为 31014 / 24144 / 20712 / 18065 个三角面。保留衬衫内外层、鞋面和头颈边界，头发采用较保守的简化比例，避免远景露出内衣或头皮。

贴图使用原始身体、2012 衣服、共用眼睛、头发和孟柏汝发丝透明遮罩。身体 ORM 转为金属度/光泽度/AO。缺失的衣服 ORM、眼睛法线、饰品材质参数使用保守值；眼镜用原始镜片几何和透明浅灰色。细节与限制见 reports/material_recovery.json。原作的特殊材质效果不保证完全相同。

目录：input 原始输入；source 可编辑 Blend/FBX；tex 相邻纹理；tools 专用脚本；build 缓存；reports 检查和最终包预览；module/BoRuModern 游戏模块；dist 交付包。

制作顺序：`prepare_model.py` → `prepare_textures.py` → `create_source.py`（Blender）→ `export_geometry.py`（Blender）→ `build_package.py` → `verify_release.py` → `render_final.py`（Blender，分别传 `-- 0/1/2/3`）→ `verify_source.py`（Blender）。使用工作区共用打包和安装入口，模组 ID 为 BoRuModern。Blender 后台脚本使用 `--python-exit-code 1`，当前会话需获准在沙箱外运行。

工具依赖为 Blender 5.2、Python NumPy/Pillow/SciPy、工作区 tools/asset_helpers、本机 mbtool/AssetTool/.NET 与当前安装的 Native 资源模板。不修改其他模组或 Native，不启动游戏，不上传远程。游戏测试由用户完成；离线检查不证明游戏中的武器握持、马匹碰撞、IK、体型滑块或所有穿模。整套装备以固定体型外观为目标，混搭不在本版兼容范围。
