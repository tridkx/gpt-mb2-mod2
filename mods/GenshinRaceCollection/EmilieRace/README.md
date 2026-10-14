# Emilie Race

艾梅莉埃完整人物固定外观种族，模块 ID `EmilieRace`，内部种族 ID `emilie`，启动器英文名 `Emilie Race`。针对本机 Native v1.4.8 制作，源模型来自米哈游，MMD 改造署名观海。

## 使用

[Mod 包](dist/EmilieRace_Mod.zip) 解压到游戏 `Modules`，在 Native、SandBoxCore、Sandbox 后启用 Emilie Race。本机安装位置为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/EmilieRace`。

新增独立女性测试兵种 `emilie_test`（艾梅莉埃），保留原版招募与兵种树。在启用作弊模式和开发者控制台的测试存档中使用：

```text
campaign.give_troops emilie_test 10
```

兵种拼装器可选择种族 `emilie`、女性，并移除头部、身体、腿部、手套和披风防具，保留需要的武器与坐骑。角色自带衣服与双手；普通防具可能叠加或遮盖外观。使用本种族的存档依赖该模块，建议单独保留测试存档。

## 外观与布料

保留源模型比例、固定脸、短发、帽子、眼镜、服装、UV 和主要颜色贴图。统一单位换算为每源单位 0.08 米，静态含帽总高约 1.729 米；自有 28 骨绑定骨架适配源关节位置及手臂方向，沿用原生动作。

**裙子不启用布料模拟**，主裙、内层、裙边、袖子、短发和非目标饰物采用普通蒙皮。仅帽后长饰和背后两条飘带启用布料；末端装饰通过同一代理跟随。三条分支分别保留头部或上身固定区，不互相连接约束。四级渲染 LOD 分别含映射数据，共用一个模拟代理。参数见 `tools/model_config.json`，结构与映射检查见 [报告](reports/mapped_cloth.json)。

预览运行组件仅修正本种族的人物展示骨架与动作集，日志位于文档目录 `Mount and Blade II Bannerlord/EmilieRace`。场景动作集从当前 Native 目录完整注册。

## 当前限制与验收

固定外观，无捏脸形变、面部表情或手指握持形变。源资产使用颜色贴图、平坦法线和保守材质控制，MMD toon 与高光效果不直接等同于游戏材质。裙子在骑乘、深蹲和大幅动作中的穿模与变形仍需实机检查。

游戏测试由用户完成：队伍、百科、物品栏人物预览，战场待机、跑动、挥击、持弓、骑乘，以及不同距离的布料效果。离线回读和动作扫描不能证明实际游戏求解、IK、握持或全部碰撞。

共用 CPU 诊断器尚不支持映射布料，渲染映射项记录为 `incomplete`；另检查直接模拟代理的待机、跑步和骑乘轨迹。代理检查提示局部碰撞与拉伸风险（`needs_review`），已查看最差帧的近似映射画面并保留原始指标，不能记作动态通过。代理诊断不代表渲染映射或游戏验收通过。当前诊断采样暂按 60 fps，尚未对齐全部游戏片段播放速度。检查汇总见 [离线报告](reports/release_validation.json)、[布料诊断](reports/cloth_diagnostics.json)、[近似映射预览](reports/cpu_mapping_preview.json)；[游戏验收状态](reports/game_acceptance.json)独立记录。

## 工程与重建

本工程位于 `mods/GenshinRaceCollection/EmilieRace/`。合集目录仅作为系列容器。`input/original/` 保留原始 PMX、贴图和作者说明；`source/` 保存可编辑 Blend/FBX，`tex/` 为相邻贴图目录。模型脚本与参数在 `tools/`，运行模块在 `module/EmilieRace/`，中间缓存、报告和交付分别在 `build/`、`reports/`、`dist/`。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow）、.NET 10、.NET Framework 4.7.2 引用程序集、当前游戏资源、mbtool、已安装 MMD Tools PMX 读取器及工作区共用 `tools/asset_helpers/`、`tools/cloth_compiler/`、`tools/cloth_simulator/`。PMX 读取器路径在模型配置中，不复制技能或插件目录到工程。

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/GenshinRaceCollection/EmilieRace/tools/rebuild.py
```

重建只生成和离线检查本模块。打包安装使用工作区 `tools/install_release.ps1 -Mod EmilieRace -Version v0.1.0`。源包保持 `source/` 与 `tex/` 相邻，并附带所需共用工具；独立展开时将 `workspace_tools/` 恢复到工作区根 `tools/` 并调整外部依赖路径。

源模型作者说明禁止二次配布；当前工程及交付包用于个人本地适配，不上传远程。[原始使用说明](input/original/readme【一定要看】.txt)、[更新日志](CHANGELOG.md)。
