# Tianxiang Renqiu v1.0.1

“纫秋为佩”完整角色皮套装备，独立 Module ID 为 `TianxiangRenqiu`，资源前缀为 `rq1_`。模组管理器显示英文名，游戏内装备名称使用中文。原始 FBX 没有骨架；本版按此模型的解剖标记适配本机原生 28 骨 human skeleton，保留原作脸型、发型及纤细轮廓。

## 穿戴与安装

Mod ZIP 顶层为 TianxiangRenqiu，可解压到游戏 Modules。依赖 Native、SandBoxCore、Sandbox；启用 Tianxiang Renqiu 后使用以下三件装备：

- 纫秋为佩 · 发容（头盔槽，`rq1_head`）
- 纫秋为佩 · 衣裙与手饰（身体槽，`rq1_body`）
- 纫秋为佩 · 腿部与绣鞋（靴子槽，`rq1_legs`）

三件配套穿戴，手套和披肩槽先留空，避免其他装备叠在皮套上。三件均注册为可交易、可用于平民装的装备；商店何时刷新由游戏决定，测试时可使用你已有的装备获取方式。脸是头部装备的固定造型，不含原版捏脸或面部表情形变。

## 当前材料

睫毛片 mesh_03 使用修正后的 V 方向、0.4 阈值透明裁切和 no_alpha_blend；原始贴图保持不变。

## 验证范围

最终 TPAC 已重新导出四级 LOD，检查 XML、材质和贴图引用、法线与切线有限性、四骨 byte 权重、34 个跨网格皮肤接缝、完整跑步/拉弓/骑乘动作和站立采样。所有 mip 均从最终包解码；原始 FBX 和贴图副本 SHA256 与输入一致。Blend 贴图已打包，Blend 与 FBX 均重新打开检查。

裙摆、长发及袖缘的 LOD0 使用有限直接布料，远处 LOD 使用蒙皮；没有交付官方编辑器烘焙的 tcc/tcm 缓存。没有运行游戏布料求解器。裙摆腿部胶囊代理仍会提示部分动作接触，不能据此保证游戏中完全不穿模。原版体型滑块、具体武器握持、骑马碰撞、材质透明度和表情表现仍需游戏实测。游戏测试由你完成。

预览使用最终 TPAC 回读网格、量化权重、解码贴图及原生动画；布料未在游戏中求解，透明贴图预览按裁切阈值显示，不能等同于游戏材质混合效果。

## 可复现制作

模型专用参数在 tools/model_config.json；源坐标缩放为 0.013，仅为此模型适配参数，不代表原角色真实身高。源包保持 source/ 和 tex/ 相邻，原始输入位于 input/。

1. 从本机 `Modules/Native/EmAssetPackages/human/human.tpac` 导出 human_skeleton，并从 animations.tpac 导出原生动作到 reports/。
2. 后台 Blender 执行 tools/rig_model.py、tools/export_geometry.py。
3. 编译 tools/PackagePatch/PackagePatch.csproj 到 build/package_patch，然后 Python 执行 tools/build_package.py。
4. 执行 tools/verify_release.py，后台 Blender 执行 tools/verify_source.py、tools/render_review.py（参数 `-- final face`）；返修时再执行 tools/verify_eye_repair.py 比较保留的 v1.0.0 基线。
5. 工作区 tools/install_release.ps1 使用 `-Mod TianxiangRenqiu -Version v1.0.1 -PreviousVersion v1.0.0` 检查、打包并只安装此模块。

所需工具位置以已安装装备技能中的本机工具表为准。本工程依赖工作区 tools/asset_helpers、D:/mb-tools、游戏资源、Blender、Python 和 .NET 10；源包不包含这些第三方工具。

版本变化见 [更新日志](CHANGELOG.md)。
