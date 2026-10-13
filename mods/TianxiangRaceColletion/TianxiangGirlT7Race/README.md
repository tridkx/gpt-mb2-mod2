# Tianxiang Girl T7 Xue Zhi Race

第 7 套“雪芷丹华”完整人物种族资源 Mod，版本 v0.1.1，适用本机 Native v1.4.8。独立模块 `TianxiangGirlT7Race`，种族 `txgirl7`，绑定骨架 `txgirl7_skeleton`。

## 功能与使用

保留源固定脸、头发、衣服、双手和已有眼周 UV 修正。基础模型统一换算为米，下裙片另有局部间隙返修；骨架关节按本套源网格测量，手臂绑定方向适配源 A 姿势，不拉伸身体或四肢。提供四级 LOD；薄上衣和裙片保留可编辑源几何精度，其余部件按距离减面。裙片、袖片和头发使用骨骼蒙皮。

v0.1.1 针对站立预览的腿裙交叉，依据本套腿部表面、保存的游戏骨骼姿态及待机周期采样，为下裙片补局部横向间隙。裙片高度、身体、脸、腿形、骨架和全部蒙皮权重保持原样；与裙片相邻的腿部部件保留各级几何精度，避免减面改变局部表面；不是整体扩张裙子。校正量及最终四级 LOD 的面内部交叉筛查见[裙片返修](reports/preview_skirt_fit.json)与[最终包预览交叉检查](reports/preview_skirt_validation.json)。

人物预览运行组件只处理本种族的预览对象，使用自己的骨架与动作集；物品栏待机采用自然垂手候选，保留所选性别和人物数据。复用已验收的第二套入口处理机制，并单独编译和进行离线回归。

本模块只提供种族与角色资源，不添加测试兵种，不覆盖原版兵种，不修改招募池或升级树。启用后不会自动给队伍增加人物。需要配置兵种时，在 [Race Troop Builder](../../RaceTroopBuilder/README.md) 中选择 `txgirl7`；完整身体自带衣服，配置时避免叠加原版防具。

## 安装与验收

启动器英文名称为 **Tianxiang Girl T7 Xue Zhi Race**，排在 Native、SandBoxCore、Sandbox 后。各套可单独或同时启用。安装包和可编辑源包在 `dist/`。

游戏验收由用户完成，v0.1.0 已获得用户“整体没什么问题”的反馈，同时确认队伍／百科／物品栏预览存在腿裙交叉；用户于 2026-10-13 确认 v0.1.1 验收通过，见[验收记录](reports/user_acceptance_20261013.json)。配置人物后检查物品栏、队伍和百科预览，回归站立、跑步、挥刀、持弓、骑乘及 LOD 切换，重点查看肩袖、手腕、裙片和整体高度。诊断日志在系统文档目录 `Mount and Blade II Bannerlord/TianxiangGirlT7Race/ui_runtime_v0.1.1.jsonl`。含本种族人物的存档依赖本模块。

## 当前限制

固定脸，不提供捏脸形变、表情或手指动态握持。服装没有独立布料模拟和腿部布料碰撞，大幅抬腿与骑乘可能交叉。离线动作检查不能代替游戏中的握持、IK、命中范围、预览效果及全部穿模验收；Monster 尺寸仍沿用本机 Native。捏脸界面适配未纳入本次验收范围。

## 工程与重建

`input/original/` 完整保留原始输入；`input/` 根层为构建输入。`source/` 保存可编辑 Blend/FBX，与 `tex/` 相邻；`tools/` 保存本套脚本和参数，`module/TianxiangGirlT7Race/` 是游戏模块，`reports/` 保存检查与最终包预览，`build/` 和 `dist/` 分别为缓存和交付目录。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET SDK、net472 引用程序集、mbtool、AssetTool、本机 Native 和工作区共用工具。源包中的 `workspace_tools/` 恢复为工作区根 `tools/`，外部工具二进制需另行准备。各套的源 FBX、物体编号、骨架参数和 GUID 独立，不直接套用其他套数的配置。

从工作区根执行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/TianxiangRaceColletion/TianxiangGirlT7Race/tools/rebuild.py
./tools/install_release.ps1 -Mod TianxiangGirlT7Race -Version v0.1.1 -CheckOnly
```

首次安装去掉 `-CheckOnly`；从已交付 v0.1.0 升级时使用 `-PreviousVersion v0.1.0`，保留旧版安装包和源包。

证据见[最终资源检查](reports/release_validation.json)、[源文件检查](reports/source_validation.json)、[骨架与手部挂点](reports/binding_validation.json)、[种族注册](reports/registration_validation.json)、[人物预览入口](reports/ui_scope_validation.json)、[待机映射](reports/preview_idle_validation.json)、[纯蒙皮检查](reports/skeletal_skirt_validation.json)、[源测量](reports/landmark_measurements.json)和[正面预览](reports/final_rest_front.png)。版本记录见 [CHANGELOG](CHANGELOG.md)。
