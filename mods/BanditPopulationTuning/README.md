# Bandit Population Tuning

骑砍2 v1.4.8 单人战役／故事模式的独立土匪数量调节 Mod。游戏内通过 MCM 的“土匪数量调节 / Bandit Population Tuning”页面设置，参数按存档保存；进入战役后可见。

## 功能与范围

| 参数 | 默认 | 范围 | 生效时机 |
| --- | --- | --- | --- |
| 地图队伍数量倍率 | 2 | 0.25～5 | 后续生成时的目标数量上限 |
| 每队生成人数倍率 | 2 | 0.25～5 | 后续自然生成的新队伍 |
| 生成与补充速度倍率 | 2 | 0～5 | 原版夜间按缺额补队的计算；0暂停补队 |

覆盖劫匪、海寇、山贼、森林强盗、草原强盗、沙漠强盗六类自然生成地图队伍及其各级原版兵员。逃兵、任务专用队伍、藏身处驻留／首领队、海上舰队不在范围内。不修改原版文件，不启动游戏。

队伍数量调整的是原版目标上限，实际地图数量仍受藏身处、清剿和原版夜间规则影响。每队人数在原版生成完毕后只计算一次，按总人数四舍五入、至少保留1人，使用最大余数分配保留原兵种比例。旧队不重复扩编、不即时删除。数量和人数各2倍对应约4倍的目标兵力规模，补充速度2倍只加速填补缺口；新开局初始填充比例不再乘补充速度。

可独立使用；与 [Genshin Bandit Race](../GenshinBanditRace/README.md) 同时启用时，先调人数、再计算混编配额。

## 安装与卸载

前置为现有 Harmony、ButterLib、UIExtenderEx 和 MCM v5；本机已按创意工坊 MCM v5.12.3 构建。Mod ZIP 解压到游戏 `Modules/`，启动器中放在四前置和原版单机模块之后，启用 **Bandit Population Tuning**。无需原神合集，也不需要另装一份 MCM。游戏运行中不要替换 DLL。

MCM 保存后影响后续生成计算。三项设为1恢复原版倍率，速度设0暂停后续补队。卸载会恢复原版生成规则；已经扩大的队伍不会自动缩小，会自然消亡。本模块不定义新兵种或自定义存档类型；MCM设置由其原有存档行为保存。现有存档加载、卸载后读档仍需用户实测，不以离线检查代替兼容验收。

## 工程与构建

`source/Runtime/` 为运行源码，`source/Tests/` 为离线检查，`module/BanditPopulationTuning/` 为可安装模块，`reports/` 为检查报告，`dist/` 保留交付包。依赖 .NET Framework 4.7.2 开发环境、.NET SDK、Python、本机游戏 DLL 和已安装前置。

在工作区根运行：

```powershell
python mods/BanditPopulationTuning/tools/release.py --install
```

不传 `--install` 只构建检查与打包。`--game-root`、`--workshop-root` 可指定游戏及创意工坊目录。安装仅写入本模块，更新前备份旧安装到 `build/install_backups/`，不改前置、存档或其他 Mod。

## 检查与限制

离线检查覆盖六类筛选、人数守恒、最大余数分配、原版真实方法补丁、数量上限和夜间补充系数、异常退出后的作用域清理，以及 MCM 无重启设置声明。详见 [检查输出](reports/offline_tests.txt) 和 [发布报告](reports/release_validation.json)。游戏内 MCM 显示、实际队伍生成、保存读档与长期数量变化待用户验收。

替换原版土匪生成行为的其他 Mod 可能绕开入口。游戏升级后需重新核对 DLL；补丁安装失败会在菜单与本模块 `ModuleData/runtime.log` 提示，全部本模块补丁撤回。

[更新日志](CHANGELOG.md)
