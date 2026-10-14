# 仙剑奇侠传七角色种族

各角色和固定时装作为独立骑砍2种族资源模块维护。这个目录是系列工程入口，不是游戏模块。

| 模块 | 外观 | 种族 ID |
| --- | --- | --- |
| [YueQingShuRace](YueQingShuRace/README.md) | 月清疏默认时装 | `yqs_default` |
| [YueQingShuOutfit2Race](YueQingShuOutfit2Race/README.md) | 月清疏第二套时装 | `yqs2_outfit2` |
| [BaiMoQingRace](BaiMoQingRace/README.md) | 白茉晴默认时装 | `bmq_default` |
| [BaiMoQingOutfit2Race](BaiMoQingOutfit2Race/README.md) | 白茉晴第二套时装，无帽 | `bmq2_outfit2` |

## 工程布局

```text
mods/Xianjian7Race/<ModId>/
  input/                  原始角色输入
  source/                 可编辑 Blend、FBX
  tex/                    与 source/ 相邻的贴图
  tools/                  当前角色专用脚本和参数
  module/<ModId>/         独立运行模块
  reports/                当前检查、预览与历史验收记录
  build/                  当前角色缓存
  dist/                   当前与历史交付包
  mod.json                交付清单
```

新增角色或独立固定时装建立自己的 `<ModId>` 工程；使用当前模型的源比例、自定义关节和碰撞拟合，不复制其他模型的骨骼位置、胶囊尺寸、资源名或 GUID。共用资源助手和布料编译器在工作区根 `tools/`，角色脚本向上定位工作区。源包解压后保持 `source/` 与 `tex/` 相邻，将 `workspace_tools/` 恢复为工作区 `tools/`。

## 模块使用

种族模块提供完整身体、骨架、材质、布料及种族注册。兵种树、原版人物替换和测试招募内容由使用方模块负责，角色资源模块不自动修改原版兵种。模块 ID、race ID 和集成限制见各角色说明。

## 动作集注册与检查

四个模块按当前 Native human 动作集目录注册自有骨架的场景集，包括地图、举旗、野外对话、领主、酒馆和条件 NPC 职业。每个模块包含 88 个原版目录对应项、一个女性共享 poses 兼容项及保留的六个短名，共 95 项；保留已选人物预览待机。所有动态名称按实际 Monster ID 生成，race ID 和旧短名不变。

模型专用 `tools/register_module.py` 与 `tools/verify_registration.py` 使用共用 `tools/race_action_sets.py`，从当前 Native 读取目录，不硬编码 88 的跨版本数量。源包带有此脚本，`workspace_tools/` 恢复到工作区 `tools/` 后可重建。默认 CLI 只检查；补齐需显式加 `--write`，已有短名时指定 `--legacy-prefix`。例如：

```powershell
python tools/race_action_sets.py --native "D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/ModuleData/action_sets.xml" --actions "mods/Xianjian7Race/YueQingShuRace/module/YueQingShuRace/ModuleData/action_sets.xml" --prefix yqs_default --skeleton yqs_skeleton --legacy-prefix yqs
python -X utf8 -m unittest discover -s tools/tests -p test_race_action_sets.py
```

各角色 `reports/action_sets_validation.json` 检查名称、继承、骨架与旧待机覆盖；`reports/action_set_fix_validation.json` 保存注册修复的资源保留证据。离线覆盖不等于地图、对话及所有职业动作已游戏验收；女性 poses 的姿态、地图明暗频闪仍需实机确认。历史调研记录见[动作集检查](../../docs/reports/2026-10-14-race-action-set-audit.md)。

打包和安装仍使用工作区共用入口，例如：

```powershell
python tools/package_delivery.py --mod YueQingShuRace --version v0.3.5 --check-only
./tools/install_release.ps1 -Mod YueQingShuRace -Version v0.3.5 -CheckOnly
```

每个角色独立发布，保留旧交付包和本地 Git 标签。系列目录重构本身不改变版本；模块功能变化按角色单独发布。
