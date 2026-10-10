# Tianxiang Qingmei v1.0.1

## 使用与穿戴

“轻梅映雪”完整角色装备，独立模组 ID `TianxiangQingmei`，资源前缀 `qm3_`。管理器英文显示，装备名称中文。

三件配套：轻梅映雪 · 发容（头盔）、轻梅映雪 · 衣裙与手饰（身体）、轻梅映雪 · 腿部与绣鞋（靴子）。手套和披肩槽留空。依赖 Native、SandBoxCore、Sandbox。Mod ZIP 顶层可解压至 Modules。

启用天香合集时，不要同时启用本套独立模块。合集使用说明见 [天香合集](../../README.md)。

## 模型与参数

原始输入保存在 input/，原始贴图在 tex/。每套独立测量的物体计划、解剖标记、UV 修正和布料参数在 tools/model_config.json，测量证据在 reports/source_inspection.json。不是物理身高的源坐标按 0.013 比例适配原生 28 骨 human skeleton。固定脸型，不提供原版表情变形。

裙摆权重配置为 pelvis_0.9_0.45：下裙摆平滑跟随同侧小腿，中心小腿影响平滑归零。四级 LOD 保留裙摆与腿部轮廓，source/SkirtClearanceFit.npz 保存可重建权重。

## 验证范围与限制

最终 TPAC 回读验证四级 LOD、量化权重、跨网格皮肤接缝、原生站立/跑步/拉弓/骑乘；贴图所有 mip 从最终包解码。Blend 打包贴图，FBX 重新导入，原始 FBX 和 PNG 哈希不变。预览来自最终 TPAC，透明按阈值裁切。LOD0 有有限布料距离，远处仅蒙皮；未运行游戏布料求解器。腿部代理接触只是诊断，游戏中裙摆、武器握持、体型滑块和骑乘碰撞仍需实测。游戏测试由你完成。

完整跑步、拉弓、骑乘及 16 个待机采样检查最终 TPAC。离线腿部接触与变形指标见 reports/reference_skirt_validation.json；游戏布料未验证，不能声称全部穿模已消除。游戏测试由用户完成。

## 重建

重建：后台 Blender 执行 tools/rig_model.py、tools/export_geometry.py；编译 tools/PackagePatch 到 build/package_patch；Python 执行 tools/build_package.py、tools/verify_release.py；后台 Blender 执行 tools/verify_source.py、tools/render_review.py -- final face；Python 执行 tools/prepare_delivery.py。工作区 tools/install_release.ps1 -Mod TianxiangQingmei -Version v1.0.1 用于检查、打包和安装自己的模块；先加 -CheckOnly 检查，实际更新时按被替换交付的真实版本提供 -PreviousVersion。源码包保持 source/ 与 tex/ 相邻；外部工具和原生游戏资源不随源包交付。本地 Git，不上传远程。

模型脚本以本套工程目录为运行目录；工作区共用安装器命令以工作区根为运行目录。

## 历史记录

版本变化见 [更新日志](CHANGELOG.md)。
