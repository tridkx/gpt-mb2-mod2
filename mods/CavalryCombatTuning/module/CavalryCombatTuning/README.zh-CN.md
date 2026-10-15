# Cavalry Combat Tuning

独立单机数值 Mod，面向本机《骑马与砍杀2：霸主》v1.4.8。战役／故事模式与自定义战斗使用的原版属性模型均已接入，村庄民兵调整用于战役／故事模式；不修改 Native 文件、兵种装备或增加自定义存档字段。

## 功能与默认值

- 所有坐骑的基础冲撞伤害乘以 **2.5**，玩家与双方 AI 同样适用。技能固定加值、护甲与取整仍由原版处理，因此最终扣血不保证严格为 2.5 倍；不影响骑枪与其他武器伤害。
- 玩家与双方 AI 骑乘使用**弓或弩**时，移动精度惩罚乘以 **0.7**，即降低 30%。不要求兵种属于骑射编队，以当前是否骑乘、当前手持武器为准。
- 仅降低随移动产生的惩罚；基础散布、持弓不稳定、转向惩罚、AI 提前量和射速维持原版。步射与投掷不变，不解锁原本无法骑乘使用的武器。
- 村庄民兵正向补充默认 **×2**，每日额外 **+0**，默认作用于**全部正常村庄**；退休率、民兵兵种、城镇和城堡保持原版。
- 六个参数接入 MCM 全局菜单，无需重启或开新档。战斗设置保存后在下一次战斗属性刷新时生效，民兵设置影响后续每日增长。设置跨存档共用。

## 安装与使用

安装包解压到游戏的 `Modules/` 下，得到 `Modules/CavalryCombatTuning/SubModule.xml`。启用 Harmony、ButterLib、UIExtenderEx、Mod Configuration Menu v5 四前置；启动器将 **Cavalry Combat Tuning** 放在 MCM、Native、SandBoxCore、Sandbox 后，使用自定义战斗时也放在 CustomBattle 后。

本机已按创意工坊 Harmony v2.4.2.248、MCM v5.12.3 及其依赖编译检查，不重复打包前置 DLL。发布工具升级旧安装前会备份，并移除本模块旧版自带的 Harmony DLL，不修改四前置目录。若下载的 DLL 被 Windows 标记阻止，打开文件属性解除阻止。停用本 Mod 后恢复原版计算，不需要清理存档。

## 数值配置

在主菜单或暂停菜单打开 **模组选项／Mod Options**，选择 **Cavalry Combat Tuning（骑兵战斗调整）**，在“冲撞”“骑射”“村庄民兵”分组中调整并保存／确认。

菜单编辑中的未保存值不改变运行设置；保存事件生成新的运行配置，之后的属性刷新／民兵增长计算使用新值，不重算已经发生的伤害或已过去的每日增长。MCM 使用固定 ID `CavalryCombatTuning_v1`、`json2` 格式持久化，文件由 MCM 管理在用户文档下 `Mount and Blade II Bannerlord/Configs/ModSettings/Global/CavalryCombatTuning/`。

| 参数 | 含义 | 允许范围 |
| --- | --- | --- |
| `ChargeDamageMultiplier` | 冲撞基础伤害倍率，1 为原版，2.5 为默认 | 0～10 |
| `MountedMovementPenaltyMultiplier` | 骑乘弓弩的移动精度惩罚倍率，1 为原版，越小越准 | 0～3 |
| `MountedAccuracyAIOnly` | true 仅加强 AI 骑射；false 同时包括玩家。对冲撞范围没有影响 | true／false |
| `VillageMilitiaRecruitmentMultiplier` | 村庄正向补充倍率，默认2；1为原版 | 0～10 |
| `VillageMilitiaDailyBonus` | 村庄每日额外人数，默认0；独立加在倍率后，可为小数 | 0～100 |
| `VillageMilitiaPlayerClanOnly` | false：全部正常村庄；true：仅当前属于玩家家族的村庄，默认false | true／false |

移动惩罚倍率可尝试：`0.85` 轻度、`0.7` 默认中等、`0.5` 较强。`0` 只消除移动惩罚这一项，不代表必中；命中率不会按倍率线性增长。

### 村庄民兵

正常村庄的每日变化：

```text
(0.5 + 炉灶数/400) × 正向补充倍率 + 每日额外人数 − 当前民兵数×0.025
```

通过给原版结果追加“补充倍率差额＋额外人数”实现，不对净增长整体乘倍数；退休项保留。增长提示中列出“骑兵战斗调整：村庄民兵补充”。被劫掠等非正常状态村庄不添加倍率或额外人数。

600炉灶村庄忽略其他影响：原版每天正向补充2人、平衡约80人；默认每天正向补充4人、平衡约160人。现有人数不会立刻翻倍，人口随每日增长逐步接近平衡。

“仅玩家家族”按计算时的当前所有者判断，不包括同王国其他家族；易主后重新判断。将正向倍率设为1、额外人数设为0即可恢复原版民兵增长规则。已生成的民兵随正常存档保存，恢复原版或停用后会按原版增长／退休逐步调整，不强制删除现有民兵。

### 旧版配置与回退

`Modules/CavalryCombatTuning/ModuleData/settings.xml` 保留为首次创建 MCM 配置时的初始值和 MCM 连接失败时的回退。第一次使用菜单会沿用旧 XML 中的数值；已有 MCM 保存值优先。后续调整请使用菜单，修改 XML 不会覆盖 MCM 已保存的值。菜单默认预设以该 XML 初始值为基础。

旧 XML／MCM 配置缺少新增参数时，使用新参数的默认值，不覆盖已有战斗参数。XML 格式错误、未知字段或超出范围会回退到默认值，原文件保留，并在菜单提示、`ModuleData/runtime.log` 记录原因。MCM 连接失败时继续使用 XML 配置，日志会明确说明。

## 源码与构建

目录：`source/Runtime/` 运行组件；`source/Tests/` 离线回归；`module/CavalryCombatTuning/` 可安装模块；`tools/release.py` 构建／检查／打包／安装；`reports/` 检查记录；`dist/` 安装包与源码包。更新记录见 [CHANGELOG](CHANGELOG.md)。

依赖 Windows、.NET Framework 4.7.2 开发环境、.NET SDK、Python 3.9+、本机游戏 DLL 和已安装四前置。默认游戏根目录为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord`；发布工具按模块 ID 从游戏 `Modules/` 与 Steam 创意工坊目录定位前置，不修改它们。

在本工程根目录执行：

```powershell
python tools/release.py --install
# 其他安装位置：
python tools/release.py --game-root "E:/Games/Mount & Blade II Bannerlord" --install
# 创意工坊不在游戏对应 SteamLibrary 时，可指定：
python tools/release.py --workshop-root "D:/SteamLibrary/steamapps/workshop/content/261550" --install
```

不传 `--install` 只构建检查和打包。工具只写入自己的游戏模块，更新前备份整个旧模块到 `build/install_backups/`，保留已安装的用户配置；交付包按时间戳保留。此工程是纯代码 Mod，使用自己的发布入口，不依赖共用 TPAC 资源打包流程。

## 实现与当前验证范围

补丁在初始菜单阶段、游戏模块加载完成后安装，从当前已加载的程序集查找 SandBox 模型，不按短名称重新加载模块 DLL；无初始菜单的宿主在任务初始化前补装。安装有去重保护。Harmony 为 `SandboxAgentStatCalculateModel.UpdateAgentStats`、`CustomBattleAgentStatCalculateModel.UpdateAgentStats` 添加后置补丁。原模型每次重建属性后，再将坐骑的 `MountChargeDamage` 或骑乘弓弩的 `WeaponMaxMovementAccuracyPenalty` 乘以对应倍率。初始化经原版调用同一更新入口，不重复挂初始化补丁，避免叠乘。`DefaultSettlementMilitiaModel.CalculateMilitiaChange` 后置补丁仅为符合范围的正常村庄追加补充差额，保留原结果与说明。MCM 在初始菜单阶段连接，响应 `SAVE_TRIGGERED`／`LOADING_COMPLETE` 更新配置快照；卸载时解绑事件。

离线验证包括：实际 v1.4.8 三个方法挂接／卸载、213 项断言、模块加载顺序与延迟安装、重复初始化去重、六个 MCM 控件和免重启标记、旧配置初值、保存事件与数值联动、村庄正向补充／退休分离、状态与归属筛选、平衡人数、增长说明、事件解绑、配置异常、安装包回读及安装文件 SHA-256 一致性。测试不启动游戏，也不替代用户实机验收；启动修复后的主菜单结果、保存后的实战／每日增长变化及跨次启动持久化待用户确认。[MCM 开发文档](https://mcm.bannerlord.aragas.org/articles/MCMv5/mcmv5.html)介绍设置发现和保存事件。

## 注意事项

- 完全替换原版属性／民兵模型、跳过原版更新或覆盖同一属性的其他 Mod，可能改变结果；本版按原版模型检查。补丁未能挂接时菜单和日志会明确提示。
- 此版本不支持联机或专用服务器。游戏升级后应重新构建、核对并测试，不能直接推断兼容。
- 本工程的 README 链接指向源码工程。安装目录中的 `README.zh-CN.md` 是其副本，源码构建和报告请从源码包查看。
