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

打包和安装仍使用工作区共用入口，例如：

```powershell
python tools/package_delivery.py --mod YueQingShuRace --version v0.3.0 --check-only
./tools/install_release.ps1 -Mod YueQingShuRace -Version v0.3.0 -CheckOnly
```

每个角色独立发布，保留旧交付包和本地 Git 标签。系列目录重构本身不改变版本；模块功能变化按角色单独发布。
