# 骑砍 2 多模组工作区

一般模组在 `mods/<模组名>/` 中独立维护。天香八套已归入 [Tianxiang Collection](mods/TianxiangCollection/README.md)：运行模块在 `mods/TianxiangCollection/module/TianxiangCollection/`，八个完整原工程在 `mods/TianxiangCollection/sets/<原模组名>/`，合集交付包在其 `dist/`。其他模组布局保持原样。

原 `mods/TianxiangT5/` 及七套校服工程统一映射到 `mods/TianxiangCollection/sets/<原ModId>/`。单套原始输入、用户修改、缓存、历史报告、旧交付包与 Git 标签保留。下文的初次迁移记录保留其生成时路径；当前命令用此新路径，共用打包与安装入口仍可使用原单套 ID。目录整理不改变各单套版本。

```text
mods/<模组名>/
  mod.json                 模组 ID、源包清单、最终 TPAC 和发布检查报告
  input/                   原始输入，保留原文件
  source/                  可编辑 Blend 与导出 FBX
  tex/                     贴图，与 source/ 保持相邻层级
  tools/                   此模型专用制作、返修和验证脚本
  module/<模组名>/         可直接安装的游戏模块
  build/                   中间文件、基线缓存（不进 Git）
  reports/                 检查结果和预览（日志不进 Git）
  dist/                    发布 ZIP 和旧版交付包（不进 Git）
tools/                     共用 AssetTool、asset_helpers、新建工程、预检、打包与安装入口
maintenance/               本机启动修复脚本、历史报告及原文件备份
docs/                      工作区说明与技能审查记录
```

## 新增模组

生化危机系列工程集中在 `mods/ResidentEvil/<ModId>/`，每个子工程独立保存 source/tex、缓存与交付。共用打包和安装入口按英文模组 ID 查找该分组；当前艾达默认服装为 [REAdaWongDefault](mods/ResidentEvil/REAdaWongDefault/README.md)。

在本目录运行 `python tools/new_mod.py NewMod`。它创建独立目录和 `mod.json`，不会复制天香的模型、参数、资源名或 GUID，也不会生成假定可用的游戏模块。模组名只使用英文字母、数字、下划线和连字符。

将原始模型放入新工程的 `input/`，贴图放入 `tex/`。按实际模型制作专用脚本，建立 `module/NewMod/SubModule.xml` 和装备 XML，使用独立资源命名空间。完善 `mod.json` 的源包文件清单、最终包和检查报告路径。

共用打包入口：

```powershell
python tools/package_delivery.py --mod TianxiangCollection --version v1.0.0 --check-only
python tools/package_delivery.py --mod TianxiangCollection --version v1.0.0
```

第一条只检查输入；第二条生成并逐项验证 ZIP。Mod ZIP 顶层是模组名，源包保留 `source/` 与 `tex/` 层级。重新发布前保留原有压缩包。

安装入口：

```powershell
./tools/install_release.ps1 -Mod TianxiangCollection -Version v1.0.0 -CheckOnly
```

实际安装需去掉 `-CheckOnly`，已有交付包时必须提供 `-PreviousVersion`；可用 `-GameRoot` 和 `-Python` 覆盖本机路径。安装前核对配置中的报告版本与最终 TPAC SHA256，准备并验证交付包，再仅复制自己的模块。它不会自动提交 Git 或打标签。发布时使用 `TianxiangT5/v1.3.1` 这类带模组名的标签；本次只迁移工程，不新建发布标签或更改游戏文件。

## 共用布料编译器

[tools/cloth_compiler](tools/cloth_compiler/README.md) 保存 TPAC 布料预处理格式、离线编译、回读验证与插入工具，支持直接模拟；模型的固定根部策略、资源名、骨骼、材料和 LOD 配置留在各模组 tools 中。明玉 v1.0.4 的近距离效果已由用户确认，LOD1 和远距离范围尚未确认。共用实现不硬编码明玉网格名或四网格数量。

源包可以在 mod.json 中配置 `shared_source_files`（仅允许工作区 tools 内文件）；打包器将其收录到 `workspace_tools/`，保持 source/tex 原层级。旧版包、版本和标签保留；此次工具迁移不改游戏模块。

## 技能的唯一维护位置

只维护 `C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/`。工作区不保存技能副本。[只读审查记录](docs/equipment_skill_review.md)列出本次发现。

Codex 中的技能已对齐此多模组布局。以下表格保留旧工程路径映射，供读取历史报告或旧版本时使用：

| 旧路径 | 新路径 |
| --- | --- |
| `tools/rig_model.py` 等天香专用脚本 | `mods/TianxiangT5/tools/` |
| `model.fbx` | `mods/TianxiangT5/input/model.fbx` |
| `inspection.blend` | `mods/TianxiangT5/source/inspection.blend` |
| `source/`、`tex/`、`module/`、`build/`、`reports/`、`dist/` | `mods/TianxiangT5/` 下对应目录 |
| `tools/repair_launch.py`、`backups/` | `maintenance/tools/repair_launch.py`、`maintenance/backups/` |
| `tools/AssetTool/` | 保持原位置 |

技能预检会识别工作区中的天香示例工程；其他项目用 `--example-workspace` 明确指定。完整示例依赖检查使用 `--require-example-pipeline --check-blender-python`，包审查使用迁移后的 TPAC 路径。旧版 Git 标签不改写，现有回归检查仍读取旧标签中的 `module/TianxiangT5/...`。

共用 AssetTool 的 `patch` 仍含天香专用布料设置，新模组使用前须检查并适配；其只读检查功能可复用。

## 共用依赖合并（2026-10-08）

原 `D:/gpt-mb2-mod` 中当前模组使用的几何、贴图、骨架和动画助手及其导入依赖已合并至 [tools/asset_helpers](tools/asset_helpers/README.md)。两个模组的工具脚本按自身位置查找这些助手，不再依赖旧工程目录；原目录及旧交付文件保持不变。

| 旧依赖路径 | 当前路径 |
| --- | --- |
| `D:/gpt-mb2-mod/pipeline/{build_assets,convert_textures,paths}.py` | `tools/asset_helpers/pipeline/` |
| `D:/gpt-mb2-mod/config/spec.py` | `tools/asset_helpers/config/spec.py` |
| `D:/gpt-mb2-mod/tools/georead.py` | `tools/asset_helpers/tools/georead.py` |
| `D:/gpt-mb2-mod/previewer/baker/{skeleton,animation,__init__,config}.py` | `tools/asset_helpers/previewer/baker/` |

使用工作区入口执行完整依赖预检：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/preflight.py --require-example-pipeline --check-blender-python
```

已安装技能的原预检脚本现默认从选定工作区根的 `tools/asset_helpers/` 读取助手，工具与动画说明已同步。工作区入口只指定工作区，直接运行原预检脚本也无需传入 `--helpers`，没有旧目录依赖或回退路径。外部依赖仍包括游戏、Blender、Python、Git、.NET 和 `D:/mb-tools`（含贴图编码库 `py/bcencode.py`），本工作区仍不是完整可移植工具包。此次整理不改变模组版本或发布标签，不更新游戏安装目录。
