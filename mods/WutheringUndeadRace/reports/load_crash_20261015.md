# 2026-10-15 故事模式读档崩溃诊断

适用范围：2026-10-15 21:58（Asia/Shanghai）发生的进程30448崩溃，Native v1.4.8.119303；Wuthering Undead Race v0.1.0与Bandit Population Tuning v1.1.0同时启用。此报告为该次历史证据，不替代当前模块使用说明。

## 已确认的直接原因

转储记录 `System.NullReferenceException`，异常顶部为：

```text
BanditPopulationTuning.EnhancementPatches.Health(CharacterObject, ref ExplainedNumber)
CharacterObject.MaxHitPoints()
PerkHelper.ClearPerksForSkill(Hero, SkillObject)
Hero.ClearPerks()
HeroDeveloper.ResetCharacterStats()
StoryModeHeroes.RegisterAll()
StoryModeManager.InitializeStoryModeObjects()
CampaignStoryMode.DoLoadingForGameType(...)
```

安装中的土匪与AI强化模块，在英雄最大生命后置补丁中直接比较 `__0.HeroObject == Hero.MainHero`。本机游戏的 `Hero.MainHero` getter为 `CharacterObject.PlayerCharacter.HeroObject`，其中 `PlayerCharacter` 来自 `Game.Current.PlayerTroop`。故事模式注册兄长、重置角色属性时，玩家角色尚未设置，调用该getter会解引用空对象。

当前安装DLL与工作区模块DLL的SHA256相同：`27f0a3d7eaaa38c0248550d1440833577f9c583eb220d35a7ef7190023d96fc2`。对应源文件为 `mods/BanditPopulationTuning/source/Runtime/Enhancements.cs:113`；第116行直接调用 `Hero.MainHero`。

## 离线复现

使用当前安装的 `BanditPopulationTuning.dll`，在独立.NET Framework进程中构造：

- `Game.Current`已存在；
- `Game.Current.PlayerTroop`为空；
- 被计算角色为英雄。

反射调用原有Health方法，得到同一方法中的 `System.NullReferenceException`。此复现未加载WutheringUndeadRace运行DLL，也未启动游戏，因此该异常不需要感染者转化、军团或领主生成逻辑参与即可触发。

原始复现输出见 [离线复现](load_crash_20261015_reproduction.txt)，托管线程和异常链见 [转储线程提取](load_crash_20261015_threads.json)。复现项目保存在本模块 `build/LoadingRepro/` 缓存中。

## 另一个日志线索

同次RGL日志21:58:00.772记录 `Null object reference found with ID: wur_jianxin_lord_template`。本机MBObjectManager在注销未就绪对象时输出该消息。现有证据没有确认对象类型或未就绪原因；不得将此警告直接认定为上述异常根因。英雄模板注册仍值得后续独立检查。

感染者runtime.log只记录了启动补丁就绪，没有进入 `Campaign ready`，与崩溃发生在战役加载阶段一致。

## 修复位置与边界

直接修复位置是BanditPopulationTuning的Health补丁：先安全取得 `Game.Current?.PlayerTroop as CharacterObject`，未就绪时跳过额外生命处理，再比较角色与玩家角色；不要将 `Hero.MainHero?.CharacterObject` 当作空值保护，因为getter本身会先抛异常。修复后需补充“游戏存在但PlayerTroop未设置”的回归检查，并由用户重新读同一存档验证。

本轮为原因调查，没有更改任何已安装模块、原版文件或用户存档，没有发布新的模组版本，也没有将该存档判定为损坏。

## 原始证据位置

- `C:/ProgramData/Mount and Blade II Bannerlord/crashes/2026-10-15_13.58.05/dump.dmp`
- `C:/ProgramData/Mount and Blade II Bannerlord/logs/rgl_log_30448.txt`
- `C:/ProgramData/Mount and Blade II Bannerlord/logs/watchdog_log_30448.txt`
- 已安装模块：`D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/BanditPopulationTuning/bin/Win64_Shipping_Client/BanditPopulationTuning.dll`

完整转储和随报告附带的存档保留在原位置，不复制到交付包。
