# 骑砍 2 多模组工作区

此工作区独立维护骑砍 2 模组的原始输入、可编辑源文件、工具、运行模块和交付包。合集中的套装工程保存在各合集的 sets/ 下；生化危机工程位于 ResidentEvil/<ModId>/，仙剑7角色工程位于 Xianjian7Race/<ModId>/，原神角色工程位于 GenshinRaceCollection/<ModId>/。原神系列根目录提供单一合集游戏模块，其他仅作容器的角色系列按各自入口说明安装。

## 模组导航

| 工程 | 内容 |
| --- | --- |
| [Tianxiang Collection](mods/TianxiangCollection/README.md) | 天香八套装备 |
| [Tianxiang Race Collection](mods/TianxiangRaceColletion/README.md) | 天香完整角色种族系列及单模块合集，包含 T5 成女校服 PVE 和少女八套；第八套为 PVP 配色 |
| [Shengxiu Collection](mods/ShengxiuCollection/README.md) | 明玉、白凤、素问 |
| [Zhenwu Collection](mods/ZhenwuCollection/README.md) | 真武少女八套装备 |
| [Beauty Banners](mods/BeautyBanners/README.md) | 九款彩色旗徽 |
| [BoRu Modern](mods/BoRuModern/README.md) | 孟柏汝现代衣装 |
| [BoRu Race](mods/BoRuRace/README.md) | 孟柏汝去脚版完整人物固定外观种族与独立女性测试兵种 |
| [Hanfu Blue Red](mods/HanfuBlueRed/README.md) | 蓝红汉服少女 |
| [Resident Evil](mods/ResidentEvil/README.md) | 系列工程入口，包含艾达王默认服装装备与固定外观种族 |
| [仙剑奇侠传七](mods/Xianjian7Race/README.md) | 独立角色种族资源：月清疏两套、白茉晴两套；白茉晴第二套为无帽版 |
| [天刀种族系列](mods/TiandaoRaceCollection/README.md) | 独立角色种族工程，包含碧水青鸾女性完整角色及布料 |
| [原神种族合集](mods/GenshinRaceCollection/README.md) | 22 个完整角色种族统一为一个游戏模块，各角色保留独立源工程；13 个新角色长发布料，艾梅莉埃保留帽后长饰与背后飘带布料 |
| [Modern Girl Race](mods/ModernGirlRace/README.md) | 现代少女 v6 完整人物固定外观种族与独立测试兵种 |
| [Race Troop Builder](mods/RaceTroopBuilder/README.md) | 自定义种族兵种树拼装器，Windows GUI、AI JSON/CLI、中英名称与固有护甲配置 |
| [Cavalry Combat Tuning](mods/CavalryCombatTuning/README.md) | 可调冲撞伤害与骑乘弓弩移动精度，独立单机运行模块 |

## 目录结构

```text
mods/<ModId>/
  mod.json                 模组 ID、源包清单、最终 TPAC 和检查报告
  README.md                当前使用与制作说明
  input/                   原始输入，保留原文件
  source/                  可编辑 Blend 与导出 FBX
  tex/                     贴图，与 source/ 保持相邻
  tools/                   模型专用制作与检查脚本
  module/<ModId>/          可安装的游戏模块
  build/                   中间文件与基线缓存
  reports/                 检查记录和预览
  dist/                    当前与历史交付包
  sets/                    合集内部套装工程（适用时）
tools/                     共用工具、预检、打包与安装入口
maintenance/               本机修复脚本、历史报告与备份
docs/                      工作区专题说明、更新日志与历史检查记录
```

## 新建工程

在工作区根运行 `python tools/new_mod.py NewMod`，模组 ID 只使用英文字母、数字、下划线和连字符。入口创建独立目录和 mod.json。

原始模型放 input/，贴图放 tex/；按实际模型编写 tools/ 下的脚本，建立 module/NewMod/SubModule.xml 和装备 XML，使用独立资源名和 GUID。完善 mod.json 的源包文件、最终包和检查报告清单。新工程需要自己的模型参数和断言。

## 共用工具与依赖

- [资源助手](tools/asset_helpers/README.md)：几何、贴图、骨架和动画函数。
- [离线布料编译器](tools/cloth_compiler/README.md)：直接模拟的数据生成、回读和插入；模型策略留在对应模组 tools/。
- [离线布料诊断器](tools/cloth_simulator/README.md)：最终包的近似 CPU 布料模拟、原生动作驱动、逐帧风险指标与离线回放；尚未校准到游戏求解结果。
- AssetTool 位于 tools/AssetTool/；patch 含天香专用布料参数，新模组使用前需要适配。
- [种族动作集工具](tools/race_action_sets.py)：从当前 Native 目录补齐种族场景集，保留旧名与待机覆盖；默认只检查，写入需显式 `--write`。用途和命名规则见[仙剑7动作集修复说明](mods/Xianjian7Race/README.md#动作集注册与检查)。

装备技能唯一维护位置为 `C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/`，工作区不保存技能副本。

外部依赖包括游戏资源、Blender、Python、Git、.NET 和 D:/mb-tools（含 py/bcencode.py）。具体版本及额外依赖见各工程和工具说明。

## 依赖预检

在工作区根运行：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/preflight.py --require-example-pipeline --check-blender-python
# 其他工程明确指定目录：
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 tools/preflight.py --example-workspace mods/HanfuBlueRed --require-example-pipeline --check-blender-python
```

通用预检入口在工作区根 tools/preflight.py，完整检查逻辑唯一维护在已安装技能 scripts/preflight.py，不放在具体模组目录。默认识别天香 T5 的合集套装路径；直接从独立模组或合集套装调用技能预检时，也会向上识别工作区根并读取 tools/asset_helpers/。其他助手目录使用 --helpers。预检覆盖工具和导入，不代表模型或游戏测试通过。

## 打包与安装

在工作区根运行；下列命令以 TianxiangCollection v1.0.0 为例：

```powershell
python tools/package_delivery.py --mod TianxiangCollection --version v1.0.0 --check-only
python tools/package_delivery.py --mod TianxiangCollection --version v1.0.0
./tools/install_release.ps1 -Mod TianxiangCollection -Version v1.0.0 -CheckOnly
```

第一条只检查输入，第二条生成并验证 ZIP，第三条只验证安装条件。实际安装去掉 -CheckOnly；已有交付包时需用 -PreviousVersion 指明被替换的版本。-GameRoot 和 -Python 可覆盖本机路径。安装前退出游戏和启动器。

Mod ZIP 顶层是模组 ID，源包保持 source/ 与 tex/ 相邻。mod.json.shared_source_files 可列入工作区 tools/ 文件，源包将其保存到 workspace_tools/。保留旧包，只复制任务涉及的模块；安装器不自动提交 Git 或打标签。

含布料的模组可通过 `mod.json.cloth_diagnostics` 接入[自动离线诊断](tools/cloth_simulator/README.md#接入模组制作与交付流程)：打包及安装前检查最终 TPAC，复用相同输入的报告，并将报告、最差帧和诊断源码加入源包。尚未配置的模组沿用原流程；已启用时 `--check-only` 也可能生成诊断缓存和报告，但不打包或安装。近似模拟结果独立于游戏验收状态。

共用入口支持顶层独立模组、天香单套 ID、ResidentEvil、Xianjian7Race、TiandaoRaceCollection、GenshinRaceCollection 和 TianxiangRaceColletion 内独立 ID。圣绣、真武内部套装从合集根打包和安装。

## 文档与检查边界

游戏测试由用户完成；离线回读、动作预览和布料数据检查不等同于游戏动态验证。各模组说明列出当前验收状态。

专题调研记录：[自定义种族主角的地图频闪、读档与装备隐形](docs/reports/2026-10-14-custom-race-player-research.md)（2026-10-14，适用 Native v1.4.8；证据与待验证项见报告）。

协作规范见 [AGENTS.md](AGENTS.md)。使用本地 Git，不上传远程；发布标签为 <ModId>/v<版本>。历史信息见 [更新日志](docs/CHANGELOG.md) 和 [历史路径对照](docs/historical-paths.md)。
