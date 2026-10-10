# BoRu - Modern Outfit

## 概览与穿戴

孟柏汝去脚版的独立骑砍2装备模块，版本 v1.0.3。固定外观，不包含面部表情或捏脸兼容。推荐女性角色成套穿戴：发容与眼镜、白衬衫与牛仔裤、双手与腕饰、帆布鞋。四件均为商品，也可在作弊物品列表搜索“孟柏汝”。模块管理器显示名为英文 `BoRu - Modern Outfit`。

## 输入与模型

原始网格来自 `D:/dsh-nvguiqiao/repo/models/08_孟柏汝_BoRu_女_去脚/`，贴图来自相邻原版 `08_孟柏汝_BoRu_女/textures/`。input 保存独立副本、原说明、源工具和 SHA256；原目录只读使用。原版去脚切口保留，鞋口仍需游戏动作测试。

原始 ActorX 骨架有 80 骨，适配本机实际导出的 28 骨 human skeleton。原始权重合并到原生骨骼，再以统一空间场适配绑定姿态；皮肤切口按三角面精确插值，跨装备共享位置、法线和权重。脸、头发、眼睛及眼镜固定随头；手型固定随原生手掌，未制作完整手指握持形变。短发、衬衫和长裤采用蒙皮，无游戏布料求解器。

腿部相对初始拟合基线横截面收窄 36%、前后厚度减小 15%，腿长保留；头、头发和眼镜放大 12%。鞋身和鞋底横向累计收窄 42.625%，袜口保持脚踝方案的宽度，脚长和高度保留。当前脚踝采用向袜口内部延伸 4.5cm 的连续覆盖与 calf/foot 权重场；鞋内隐藏皮肤尾段随鞋身收窄。眼白与睫毛独立处理，虹膜使用对应 UV。

四级 LOD 为 31014 / 24144 / 20712 / 18065 个三角面。保留衬衫内外层、鞋面和头颈边界，头发采用较保守的简化比例，避免远景露出内衣或头皮。

## 材料与限制

贴图使用原始身体、2012 衣服、共用眼睛、头发和孟柏汝发丝透明遮罩。身体 ORM 转为金属度/光泽度/AO。缺失的衣服 ORM、眼睛法线、饰品材质参数使用保守值；眼镜用原始镜片几何和透明浅灰色。细节与限制见 reports/material_recovery.json。原作的特殊材质效果不保证完全相同。

工具依赖为 Blender 5.2、Python NumPy/Pillow/SciPy、工作区 tools/asset_helpers、本机 mbtool/AssetTool/.NET 与当前安装的 Native 资源模板。不修改其他模组或 Native，不启动游戏，不上传远程。游戏测试由用户完成；离线检查不证明游戏中的武器握持、马匹碰撞、IK、体型滑块或所有穿模。整套装备以固定体型外观为目标，混搭不在本版兼容范围。

## 工程与重建

目录：input 原始输入；source 可编辑 Blend/FBX；tex 相邻纹理；tools 专用脚本；build 缓存；reports 检查和最终包预览；module/BoRuModern 游戏模块；dist 交付包。

专用脚本位于本工程 tools/，以本工程目录为运行目录。制作顺序：`prepare_model.py` → `prepare_textures.py` → `create_source.py`（Blender）→ `export_geometry.py`（Blender）→ `build_package.py` → `verify_release.py` → `verify_ankle.py` → `render_final.py`（Blender，分别传 `-- 0/1/2/3`）→ `verify_source.py`（Blender）。共用打包和安装入口以工作区根为运行目录，模组 ID 为 BoRuModern。Blender 后台脚本使用 `--python-exit-code 1`。

## 检查与注意事项

宽度、脚踝和鞋身回归检查分别由 verify_width.py、verify_ankle.py、verify_shoe_revision.py 执行。前两版拟合基线位于 build/width_v100/ 和 build/shoe_v102/，缓存缺失时按对应本地标签恢复。

裤口内隐藏皮肤采用平滑的横截面内收，保留连续覆盖；皮肤上切口不能通过下移来替代裤口穿模检查。

## 历史记录

版本变化见 [更新日志](CHANGELOG.md)。
