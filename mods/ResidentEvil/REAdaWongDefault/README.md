# Resident Evil - Ada Wong Default

## 概览与使用

RE4 重制版艾达王默认服装的独立骑砍2装备模块，版本 v1.0.0。目标为固定艾达外观，不包含面部表情或捏脸兼容。装备分为发容、红色针织衫与枪套、手套、长靴四件，推荐成套使用。枪械为服装装饰，不提供射击功能。

启用模块显示名 `Resident Evil - Ada Wong Default`。四件装备已注册为商品，商店刷新后可能出现；也可在游戏作弊物品列表按“艾达王”搜索。建议女性角色成套穿戴，固定手型未制作原生手指握持变形。高领衫与发容应成套使用，混搭和身材滑块不在本版兼容范围。

## 原始输入与工程

原始输入来自 `D:/dsh-mod/re4-remake/output/Ada_Wong/`；主线 cha200 外观保持独立副本，同款 cha800 原始网格提供解剖和权重参考。运行骨架使用本机骑砍 human skeleton；肩肘、髋膝、头颈另做解剖蒙皮修正。原始输入不覆盖。

工程：input 原始副本；source 可编辑 Blend/FBX；tex 相邻纹理；tools 模型专用脚本；module/REAdaWongDefault 游戏模块；build 缓存；reports 检查/预览；dist 交付与回退包。

## 重建与依赖

制作顺序：prepare_model.py → prepare_textures.py → create_source.py（Blender）→ export_geometry.py（Blender）→ build_package.py → verify_release.py → render_final.py（Blender）→ verify_source.py（Blender）→ 打包安装。使用工作区共用 `tools/package_delivery.py` 和 `tools/install_release.ps1`，模组 ID 为 REAdaWongDefault。

外部依赖：Blender 5.2、Python NumPy/Pillow/SciPy、本工作区 tools/asset_helpers、本机 mbtool/AssetTool、`D:/dsh-mod/re4-remake/tools/RE-Mesh-Editor-main` 解析库，以及当前骑砍游戏模板。解码时仅复制和读取原资源，不修改提取工程。

专用脚本以本工程目录为运行目录，共用打包和安装入口以工作区根为运行目录。

## 材料与验证限制

材质限制记录在 reports/material_recovery.json：缺失的主线 PBR 贴图使用平法线与保守材质参数；缺失的原始头发/睫毛透明遮罩不伪造，暂以不透明材质显示。当前源文件外观不能等同完整还原 RE 原作 shader。

短下摆采用骨骼随动，本版未添加游戏布料模拟。离线检查不替代游戏的握持、骑乘碰撞、IK 或体型缩放测试。游戏由用户测试；不修改 Native，不启动游戏。
