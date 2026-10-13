# Tianxiang Race Collection

单一可安装的天香完整人物种族合集，模块 ID `TianxiangRaceCollection`，版本 v0.1.0，适用本机 Native v1.4.8。包含 T5 PVE 成女及少女八套，在启动器只需启用 **Tianxiang Race Collection**。

## 使用与范围

合集直接复用九套已交付的 TPAC 和人物预览组件，保留各自种族 ID、骨架、材质、贴图、动作集、身体比例和护甲设定。没有重新绑骨、修改模型或新增兵种。第一、二套原有测试兵种和第一套布料碰撞注册保留；少女 3–8 套保持纯蒙皮和 v0.1.1 的站立裙片返修，第八套为 PVP 配色。

| 角色 | 独立工程基线 | 种族 ID |
| --- | --- | --- |
| T5 成女 PVE | TianxiangT5PVERace v0.1.2 | `txt5pve` |
| 纫秋为佩 | TianxiangGirlT1Race v0.1.6 | `txgirl1` |
| 沐风为裳 | TianxiangGirlT2Race v0.1.3 | `txgirl2` |
| 轻梅映雪 | TianxiangGirlT3Race v0.1.1 | `txgirl3` |
| 暮雨亭兰 | TianxiangGirlT4Race v0.1.1 | `txgirl4` |
| 芳姿盈袖 | TianxiangGirlT5Race v0.1.1 | `txgirl5` |
| 碎梦繁花 | TianxiangGirlT6Race v0.1.1 | `txgirl6` |
| 雪芷丹华 | TianxiangGirlT7Race v0.1.1 | `txgirl7` |
| 臻姿凤仪 PVP | TianxiangGirlT8Race v0.1.1 | `txgirl8` |

详细角色功能、模型限制和独立工程见[系列入口](../README.md)。少女 3–8 套 v0.1.1 已获用户验收；合集本身仍需用户进行单模块加载验证。

## 安装与启动器

安装包为 `dist/TianxiangRaceCollection_Mod.zip`，ZIP 顶层是 `TianxiangRaceCollection/`，可解压到游戏 `Modules/`。启动器勾选与排序由用户处理，本工程不修改启动器配置、不启动游戏。

启用合集，排在 Native、SandBoxCore、Sandbox 后；取消九个独立模块的勾选。合集和独立模块包含相同种族与资源，不能同时启用。原独立工程、已安装目录及旧交付包均保留，便于回退。

在 [Race Troop Builder](../../RaceTroopBuilder/README.md) 中选择合集作为种族提供模块，使用上表原种族 ID；新生成的兵种配置依赖 `TianxiangRaceCollection`。已有兵种配置若声明依赖独立模块 ID，需要另外调整其依赖，本次没有修改其他兵种模块。

## 检查与存档切换

离线检查核对九个 TPAC 和九个预览 DLL 的字节一致性，逐项比较合并后的种族、动作、Monster、布料碰撞和测试兵种定义；原版兵种没有覆盖。Race Troop Builder 已确认能从一个合集模块发现全部九个种族。

用户游戏阶段只启用合集，检查启动、种族显示、队伍／百科／物品栏预览及第一套布料表现。角色和兵种 ID 保留，但模块 ID 从独立模块变为合集；本次未迁移存档或修改存档中的模块清单，旧存档切换应先在副本上验证。

诊断日志沿用各角色的独立目录和版本名称。具体文件位置见对应独立工程 README。

## 工程、源包与重建

本工程的 `tools/components.json` 定义九套基线；`source/manifest.json` 记录来源版本和资源哈希；`module/` 保存可安装合集；`reports/` 保存合并、目录发现与交付证据。合集工作区直接引用九个独立工程的源文件，不复制一份模型到仓库。

`dist/TianxiangRaceCollection_Source.zip` 是完整可编辑工作区，包含九套原始输入、Blend/FBX、贴图、模型参数、构建脚本、组件模块以及共用工具。解压后保留 `mods/` 与 `tools/` 层级；各组件的 `source/` 和 `tex/` 仍相邻。重新拼合集只需 Python 标准库；重新制作单个模型需其 README 所列的 Blender、.NET、mbtool、AssetTool 和当前游戏资源。

从工作区根执行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/TianxiangRaceColletion/TianxiangRaceCollection/tools/build_collection.py
./tools/install_release.ps1 -Mod TianxiangRaceCollection -Version v0.1.0 -CheckOnly
```

首次安装去掉 `-CheckOnly`；安装后执行 `mods/TianxiangRaceColletion/TianxiangRaceCollection/tools/package_sources.py` 生成完整可编辑合集源包。升级需指定实际旧版 `-PreviousVersion`，保留旧包。

证据见[合集检查](reports/release_validation.json)、[种族目录发现](reports/race_catalog_validation.json)和[源包检查](reports/source_delivery_validation.json)。变更见 [CHANGELOG](CHANGELOG.md)。
