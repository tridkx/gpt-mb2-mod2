# Tianxiang T5 PVE Race

天香 T5 成女校服 PVE 完整角色种族，当前版本 `v0.1.0`，适配本机 Bannerlord Native `v1.4.8`。固定保留原模型的脸、头发、身体、双手和白粉配色服装；以自有骨架沿用原生动作，源网格只做厘米到米的统一换算，含头饰总高约 1.654 米。

## 使用

模块 ID 为 `TianxiangT5PVERace`，启动器显示名为 `Tianxiang T5 PVE Race`，内部种族 ID 为 `txt5pve`。依赖 Native、SandBoxCore、Sandbox，放在这些模块之后加载。

安装目录：`D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/TianxiangT5PVERace/`。`dist/TianxiangT5PVERace_Mod.zip` 顶层为该 Module，可解压到游戏 Modules。

本模块提供独立种族资源，不替换原版兵种，也不加入招募入口或玩家种族选择菜单。可在 [Race Troop Builder](../../RaceTroopBuilder/README.md) 中把 `txt5pve` 分配给所选兵种，使用成年女性设置，保留武器与坐骑，去掉会覆盖完整角色身体的防具。生成的兵种模块需依赖本模块；自定义种族存档后续仍需保留该依赖。

## 工程与重建

`input/` 保存指定目录的 PVE FBX、OBJ、MTL 和原始说明；`source/` 保存绑定后的 Blend、FBX；`tex/` 保存 PVE 与共用贴图。`tools/` 是本模型的绑定参数、注册、资源构建、界面适配和检查脚本；`module/`、`build/`、`reports/`、`dist/` 分别是游戏模块、缓存、检查与预览、交付包。

依赖 Blender 5.2、Anaconda Python（NumPy、SciPy、Pillow、lxml）、.NET 10 SDK、.NET Framework 4.7.2 引用程序集、本机游戏 DLL/XML、`D:/mb-tools` 及工作区共用资源助手。脚本向上定位工作区，不依赖固定目录深度。源 ZIP 中的 `workspace_tools/` 还原到工作区根 `tools/`，保持项目 `source/`、`tex/` 层级。

在工作区根执行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/TianxiangRaceColletion/TianxiangT5PVERace/tools/rebuild.py
./tools/install_release.ps1 -Mod TianxiangT5PVERace -Version v0.1.0 -CheckOnly
```

重建不自动安装。首次实际安装去掉 `-CheckOnly`；后续发布新版本需更新配置，并通过 `-PreviousVersion` 保留旧交付包。

## 验证与限制

最终 TPAC 回读检查覆盖引用、元数据、四级 LOD、量化权重、193 个共享接缝点、绑定骨架、全部贴图 mip，以及待机抽样和跑步／持弓／骑乘／挥砍全周期的有限值与严重拉裂检查。Blend、FBX 重开与原始模型对比确认 LOD0 源比例保留。证据见 [发布检查](reports/release_validation.json)、[源检查](reports/source_validation.json) 和 [最终包预览](reports/final_rest_front.png)。

本版本裙摆、袖带和头发采用骨骼蒙皮，没有游戏布料物理；极端动作仍可能穿模。固定脸不支持捏脸、表情或手指握持形变，身体滑块不作为支持功能。界面运行组件只修正本种族 UI 预览的骨架创建与重建，沿用人物性别、装备、位置、缩放及动作进度；战场不参与扫描。

游戏启动、人物界面首次显示与重建、队伍／百科／物品栏预览、武器握持、骑乘和战斗表现仍由用户测试。离线检查和 Blender 预览不代表游戏验收通过。

## 注意事项

源材质名虽然含 `PVP`，但 PVE FBX 与 MTL 实际引用 `tunic_D-PVE.png`、`pants_D-PVE.png`。判定版本应检查贴图路径和哈希，不按材质名选择 PVP 图。透明裁切保留贴图 Alpha，材质关闭顶点 Alpha 相乘，避免独立身体部件消失。

系列组织见 [Tianxiang Race Collection](../README.md)；版本记录见 [CHANGELOG](CHANGELOG.md)。
