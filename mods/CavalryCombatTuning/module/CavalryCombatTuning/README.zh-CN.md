# Cavalry Combat Tuning

独立单机数值 Mod，面向本机《骑马与砍杀2：霸主》v1.4.8。战役／故事模式与自定义战斗使用的原版属性模型均已接入；不修改 Native 文件，不改兵种装备与存档数据。

## 功能与默认值

- 所有坐骑的基础冲撞伤害乘以 **2.5**，玩家与双方 AI 同样适用。技能固定加值、护甲与取整仍由原版处理，因此最终扣血不保证严格为 2.5 倍；不影响骑枪与其他武器伤害。
- 玩家与双方 AI 骑乘使用**弓或弩**时，移动精度惩罚乘以 **0.7**，即降低 30%。不要求兵种属于骑射编队，以当前是否骑乘、当前手持武器为准。
- 仅降低随移动产生的惩罚；基础散布、持弓不稳定、转向惩罚、AI 提前量和射速维持原版。步射与投掷不变，不解锁原本无法骑乘使用的武器。
- 配置在游戏加载本模块时读取，修改后需完全退出并重启游戏。无需开新档。

## 安装与使用

安装包解压到游戏的 `Modules/` 下，得到 `Modules/CavalryCombatTuning/SubModule.xml`。启动器勾选 **Cavalry Combat Tuning**，放在 Native、SandBoxCore、Sandbox 后；使用自定义战斗时也放在 CustomBattle 后。

运行时自带 Harmony 2.4.2，无需另装 Harmony、MCM 或其他前置 Mod。若下载的 DLL 被 Windows 标记阻止，打开文件属性解除阻止。停用本 Mod 后恢复原版计算；不需要清理存档。

## 数值配置

编辑**游戏安装目录**中的 `Modules/CavalryCombatTuning/ModuleData/settings.xml`：

```xml
<CavalryCombatTuning>
  <ChargeDamageMultiplier>2.5</ChargeDamageMultiplier>
  <MountedMovementPenaltyMultiplier>0.7</MountedMovementPenaltyMultiplier>
  <MountedAccuracyAIOnly>false</MountedAccuracyAIOnly>
</CavalryCombatTuning>
```

| 参数 | 含义 | 允许范围 |
| --- | --- | --- |
| `ChargeDamageMultiplier` | 冲撞基础伤害倍率，1 为原版，2.5 为默认 | 0～10 |
| `MountedMovementPenaltyMultiplier` | 骑乘弓弩的移动精度惩罚倍率，1 为原版，越小越准 | 0～3 |
| `MountedAccuracyAIOnly` | true 仅加强 AI 骑射；false 同时包括玩家。对冲撞范围没有影响 | true／false |

移动惩罚倍率可尝试：`0.85` 轻度、`0.7` 默认中等、`0.5` 较强。`0` 只消除移动惩罚这一项，不代表必中；命中率不会按倍率线性增长。数值使用英文小数点。缺少的参数使用默认值；格式错误、未知字段或超出范围会使整份配置回退到默认值，原文件保留，并在菜单提示、`ModuleData/runtime.log` 记录原因。

## 源码与构建

目录：`source/Runtime/` 运行组件；`source/Tests/` 离线回归；`module/CavalryCombatTuning/` 可安装模块；`tools/release.py` 构建／检查／打包／安装；`reports/` 检查记录；`dist/` 安装包与源码包。更新记录见 [CHANGELOG](CHANGELOG.md)。

依赖 Windows、.NET Framework 4.7.2 开发环境、.NET SDK、Python 3.9+、本机游戏 DLL，以及 NuGet 的 `Lib.Harmony 2.4.2`。默认游戏根目录为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord`。

在本工程根目录执行：

```powershell
python tools/release.py --install
# 其他安装位置：
python tools/release.py --game-root "E:/Games/Mount & Blade II Bannerlord" --install
```

不传 `--install` 只构建检查和打包。工具只写入自己的游戏模块，更新前备份整个旧模块到 `build/install_backups/`，保留已安装的用户配置；交付包按时间戳保留。此工程是纯代码 Mod，使用自己的发布入口，不依赖共用 TPAC 资源打包流程。

## 实现与当前验证范围

Harmony 为 `SandboxAgentStatCalculateModel.UpdateAgentStats`、`CustomBattleAgentStatCalculateModel.UpdateAgentStats` 添加后置补丁。原模型每次重建属性后，再将坐骑的 `MountChargeDamage` 或骑乘弓弩的 `WeaponMaxMovementAccuracyPenalty` 乘以对应倍率。初始化经原版调用同一更新入口，不重复挂初始化补丁，避免叠乘。

离线验证包括：实际 v1.4.8 方法挂接／卸载、142 项数值与条件断言、配置异常处理、安装包回读及安装文件 SHA-256 一致性。测试不启动游戏，也不替代用户实机验收；尚需确认战场伤害和移动射击观感。

## 注意事项

- 完全替换原版属性模型、跳过原版更新或覆盖同一属性的其他战斗 Mod，可能改变结果；优先使用原版战斗模型。补丁未能挂接时菜单和日志会明确提示。
- 此版本不支持联机或专用服务器。游戏升级后应重新构建、核对并测试，不能直接推断兼容。
- 本工程的 README 链接指向源码工程。安装目录中的 `README.zh-CN.md` 是其副本，源码构建和报告请从源码包查看。
