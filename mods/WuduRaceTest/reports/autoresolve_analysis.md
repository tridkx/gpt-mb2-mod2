# 自动战斗机制核对

日期：2026-10-10。范围：本机 Native v1.4.8 原版战役自动模拟。其他模组替换 GameModel 时结论不保证适用。

核对文件：游戏 `bin/Win64_Shipping_Client/TaleWorlds.CampaignSystem.dll`，SHA256 `1f8e33e2ed73e6ec653d7629180afb70649ddc6e5bd1657a802a264efda1c3ae`。以 ilspycmd 回读 `DefaultMilitaryPowerModel` 与 `DefaultCombatSimulationModel`，生成的本机分析代码放于未交付的 `build/research/`。

## 基础战力

`DefaultMilitaryPowerModel.GetDefaultTroopPower` 对普通兵使用：

```text
基础战力 = (2 + Tier) × (10 + Tier) × 0.02
```

T1 为 0.66，T2 为 0.96，T6 为 2.56。英雄另有等级换算和倍率，不能把普通兵公式套给英雄。

`GetTroopPower` 继续乘以 `1 + leaderModifier + contextModifier`。领队特长影响前者，攻守、地形、攻城/村庄、步兵/弓兵/骑兵/骑射身份影响后者。类别由 `HasMount()` 和 `IsRanged` 等判断，所以装备可以间接改变兵种类别，但此基础公式不累加防具护甲或武器伤害。

## 模拟交战

`DefaultCombatSimulationModel.SimulateHit` 的基础模拟伤害是以下表达式取整，再应用战术、侦察等特长及士气修正：

```text
(0.5 + 0.5 × 随机数) × 40 × (攻击方战力 / 受击方战力)^0.7 × strikerAdvantage
```

这不是把实际场景中的武器命中、防具减伤、角色体型和动画逐一模拟。基础战力也不是最终胜率；人数、战斗环境及这些修正都会影响结果。

## 本模块的处理

`imperial_recruit` 保持等级 6、T1 和步兵身份，因此沿用 0.66 基础战力，不需要手动赋值。`WuduRaceTest.dll` 仅在初始化时记录当前模型算出的战力，不注册或替换战斗模型。

第一轮移除防具、改变网格/种族不会直接改变上述基础战力。未来添加“无装备但固有 30 身甲”，若只作用于场景护甲计算，也不会自动提高战役模拟战力。可以继续接受原版按阶级抽象的规则；只有希望自动战斗反映这种额外防御时，才需要另行实现修正，并非制作自定义种族的必需步骤。
