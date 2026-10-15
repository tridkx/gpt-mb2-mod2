# 2026-10-15 新档进入大地图故障

范围：进程11680，2026-10-15 22:10—22:13（Asia/Shanghai），游戏v1.4.8.119303，感染模块v0.1.0。用户限定本轮只修复感染模块，其他模块由另一对话处理。

## 感染模块已确认的问题

RGL日志22:11:12.106：`Null object reference found with ID: wur_jianxin_lord_template`。

安装中感染模块日志22:11:17：

```text
DISABLED: System.IO.InvalidDataException: Missing wur_jianxin_lord_template
WutheringUndeadRace.Catalog.Bind()
WutheringUndeadRace.UndeadBehavior.Session(CampaignGameStarter)
```

结合本机MBObjectManager的注销流程，可以确认该模板最终未能留在可用角色注册表中。v0.1.0的离线Schema与补丁检查没有覆盖实际引擎完成XML加载和注销未就绪对象之后的注册表，不能据此宣称当时已在游戏中正常注册。现有日志没有给出该对象被标记未就绪的完整链条。

## v0.1.1处理与证据边界

模板是提供给HeroCreator.CreateSpecialHero的CharacterObject，不是预先存在的静态Hero。生成器改为只声明 `is_template=true`，不再同时声明 `is_hero=true`；职业、ID、模型、缩放、护甲与重生逻辑保留。增加八个模板声明的回归检查。

补充CharacterObject.Deserialize完成后的本模块对象日志。此时处于AfterInitialized之前，日志中的ready=false可能是正常中间状态，不能单独视为失败。Session绑定报告全部缺失／未就绪ID，不再只报第一项；绑定失败时撤回全部本模块Harmony补丁。

这些修改修正了动态模板的声明方式并补全诊断；在用户实际重新加载之前，不认定已证明该标记是原始模板被注销的唯一根因，也不认定修复已经游戏验收通过。

## 同次转储中的独立异常

用户取消官方转储，但Windows保存了：

`C:/Users/DKX/AppData/Local/CrashDumps/TaleWorlds.MountAndBlade.Launcher.exe.11680.dmp`

其异常为 `System.IO.InvalidDataException: Troop missing: gbr_noelle`，调用链经过 `GenshinBanditRace.Catalog.Bind` → `GenshinBanditRace.Patches.Mix` → 故事模式教程结束时生成初始土匪。它与感染模块停用不是同一个异常。按用户要求，没有修改该模块，修复范围仅限感染模块。

托管线程提取见 [转储分析](new_game_crash_20261015_threads.json)。此处保留独立异常记录，是为了避免用感染模板修复声称解决了另一模块的崩溃。

## 复测

用户完全退出游戏后安装v0.1.1，重启、进入战役或故事模式。检查安装目录 `ModuleData/runtime.log`：应有48个本模块NPC反序列化记录，并出现 `Campaign ready`，不应出现不完整注册表错误。如果再次失败，读取新增的完整缺失名单与同次转储继续定位。其他模块的故障需由对应修复同时排除。

助手未启动游戏，也未改动用户存档、Native或其他模组。
