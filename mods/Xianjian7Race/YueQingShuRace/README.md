# Yue Qingshu Race

月清疏默认时装的独立种族资源模块，版本 v0.3.3，适用本机 Native v1.4.8。属于[仙剑7系列工程](../README.md)。模块 ID 为 `YueQingShuRace`，种族 ID 为 `yqs_default`。

## 功能与验收

脸、头发、默认服装、身体和双手组成完整身体，使用独立 28 骨 `yqs_skeleton`，沿用原生动作。源网格只做整体转向，保留脸、胸部、四肢及身高比例，含头饰总高约 1.676 米。提供四级 LOD，裙摆、悬垂袖片、长发、发带和流苏共 18 个布料网格，使用 56 个按源模型拟合并带局部随动的碰撞胶囊。[统计](reports/lod_stats.json)、[资源检查](reports/release_validation.json)、[源文件检查](reports/source_validation.json)。

用户已验收 v0.2.2 的效果，见[游戏验收记录](reports/game_acceptance.json)。当前沿用 v0.3.2 的模型、绑骨和布料资源。v0.3.3 仅更新 `yqs_default` 创建页与物品栏的人物预览适配，选择自有骨架及对应男女动作集，保留当前动作、动画进度和缩放。创建页使用 facegen 集，物品栏使用已配置女性垂手待机的 warrior 集。地图、战场和其他种族不在适配范围内，不增加捏脸功能。创建页倒 C 形手臂的实机结果尚待复测。离线检查没有运行游戏求解器；当前布料未通过用户验收。

不做表情、动态手势、捏脸或换装，手指保持源姿态；省略 UE 专用眼周遮挡和泪线层。固定外观含默认衣服，不能直接叠穿原版防具。

手臂绑定与几何保留见[手臂专项检查](reports/arm_binding_validation.json)。物品栏修复的离线证据见[入口与作用范围回归](reports/ui_scope_validation.json)、[动画片段 GUID 检查](reports/preview_idle_validation.json)和[完整待机循环检查](reports/inventory_pose_validation.json)。

## 安装与集成

`dist/YueQingShuRace_Mod.zip` 顶层目录可解压到游戏 `Modules/`；启动器勾选 **Yue Qingshu Race**，排在 Native、SandBoxCore、Sandbox 后。

本模块不包含兵种树、NPCCharacters 或原版兵种替换；帝国贵族新兵保持原版。独立加载不会自动生成月清疏角色，也不提供自定义种族选择界面。

其他角色或兵种模块可依赖 `YueQingShuRace`，为人物指定 `race="yqs_default"`、女性与成人年龄，使用本模块的完整身体。使用方自行配置人物/兵种的生成、数值、装备与升级；防具槽应排除会叠加或遮盖完整身体的衣服。武器和坐骑由使用方选择。已有存档若包含本种族角色，应保留本资源模块。

## 工程与重建

工程位于 `mods/Xianjian7Race/YueQingShuRace/`。原始输入在 `input/default/`，来自 `D:/dsh-xianjian7/output/月清疏_YueQingShu/01_默认套装_MAJ02_01/`，原文件保留。`source/` 保存打包贴图的 Blend 和 FBX，`tex/` 与它相邻；`tools/` 为月清疏专用脚本和参数，`module/` 为运行模块，`reports/` 为检查与预览，`reports/history/` 为历史记录，`build/` 和 `dist/` 分别为缓存与交付包。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml、Matplotlib）、.NET 10、mbtool、AssetTool、游戏资源和工作区 `tools/asset_helpers/`、`tools/cloth_compiler/`。脚本向上定位共用工具，不依赖项目目录深度。历史报告保留原路径，不能当作当前操作依据。

从工作区根运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/Xianjian7Race/YueQingShuRace/tools/rebuild.py
./tools/install_release.ps1 -Mod YueQingShuRace -Version v0.3.3 -CheckOnly
```

源包保持 `source/` 与 `tex/` 相邻，Blend 使用相对贴图路径；`workspace_tools/` 恢复到工作区根 `tools/`。检查脚本使用旧交付包作为基线，重建前保留 dist/ 内历史版本。安装与打包使用工作区共用入口，旧包保留，使用本地 Git。变更见[更新日志](CHANGELOG.md)。

## 布料参数与注意事项

`ClothDistance` 顶点色 Alpha 保存活动距离（米），网格倍率为 1，0 表示固定。材质关闭顶点 Alpha 透明度，避免固定部分消失。部件与固定点见[布料绘制](reports/cloth_paint.json)，碰撞和活动范围见[布料检查](reports/cloth_validation.json)、[臀胯覆盖检查](reports/feedback_fix_validation.json)、[分区动作覆盖](reports/panel_motion_validation.json)及[前后重力代理对比](reports/skirt_collision_validation.json)。

布料采用原生直接模拟；碰撞使用随骨骼运动的胶囊近似，裙摆保护区为原模型臀胯低于刚性腰带的区域（源 Z < 1.06 米），按三角面内外采样拟合短胶囊，基础间距 2 毫米并增加实测动作局部余量。上腹由固定腰带和蒙皮保持外观，碰撞体避开内嵌的固定裙根；保护区拟合检查需要身体处于碰撞体内部，不能用允许身体外露的正容差当作通过。离线采样和探针用于筛查，游戏反馈为实际观感依据。

当前碰撞胶囊数量高于旧版，大规模战场性能尚未实测；用户已反馈当前布料多层穿模且下落不自然；本版保持 v0.3.2 的布料资源，只更新创建页预览组件。布料仍未通过游戏验收。

简化裙摆代理已做独立试验，但候选存在映射偏移和外观问题，未纳入正式重建或安装。结果、可编辑实验源文件与复现命令见[简化代理试验报告](reports/experiments/simplified_skirt_2026-10-14/README.md)。
