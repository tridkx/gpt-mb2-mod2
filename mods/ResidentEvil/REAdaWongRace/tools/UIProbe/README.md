# 预览骨架修正与诊断

适用于 REAdaWongRace v0.1.3、Native v1.4.8。创建角色预览的实机记录表明，艾达身体曾使用 `human_skeleton` 和 `as_human_warrior`；绑定矩阵与原版 human 一致。当前游戏的捏脸重建路径创建新的 AgentVisualsData 时没有传入自定义动作集。

## 当前运行模块

`REAdaWongRace.UIRuntime.dll` 每 0.25 秒检查非战场界面中的人物预览，只处理 race 为 `reada_wong` 且实际骨架不为 `adar_skeleton` 的对象。动作集先验证属于艾达骨架；根据预览来源及性别选 facegen 或 warrior 集，重建预览骨架，保留位置、缩放和两条动画通道的动作进度。不修改原版文件、其他种族、战场 Agent、TPAC 或源模型，不使用 Harmony。

本机 v1.4.8 的 AgentVisuals 私有 Refresh 路径用于完整重建骨架；其他游戏版本需重新核对接口。扫描只遍历当前 UI 对象，数量与深度有上限。界面重建到校正之间可能短暂显示旧姿态。编译、资产一致性、修正后捏脸骨架记录与用户反馈见 [运行检查](../../reports/ui_runtime_validation.json)和[游戏验收记录](../../reports/game_acceptance.json)。

需要复核时，由用户重新启动游戏，在捏脸和物品栏／队伍／百科预览停留约十秒，然后退出。日志在用户文档目录的 `Mount and Blade II Bannerlord/REAdaWongRace/ui_runtime_v0.1.3.jsonl`，包含 `preview_repair` 和修正后的 `ada_pose`。最多采集 120 份姿态，日志上限 12 MiB。

## 仅诊断模式

相同源码编译为 `REAdaWongRace.UIProbe.dll` 时仅观察，不校正任何姿态。原 v0.1.2 诊断覆盖包 `dist/REAdaWongRace_UIProbe.zip` 与原始日志保留；它是历史诊断包，不用于覆盖当前修正版。

## 构建与回退

从工作区根构建当前运行模块：

```powershell
& 'C:/ProgramData/anaconda3/python.exe' -B -X utf8 mods/ResidentEvil/REAdaWongRace/tools/UIProbe/build_runtime.py
```

退出游戏后安装保留的 `dist/REAdaWongRace_v0.1.2_Mod.zip` 可回退到原版交付状态；其 SubModule.xml 不加载运行时校正 DLL。旧的只读诊断 DLL 已从当前模块停用。工具二进制、编译缓存和第三方依赖不包含在可编辑源包中。
