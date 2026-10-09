# 战斗结束后物品界面崩溃检查 — 2026-10-10

适用：Bannerlord v1.4.8.119303、ShengxiuCollection v1.1.7、TroopDesigner v1.3.6。用户确认明玉头发整体效果可接受；此次确认不涵盖所有动作和体型。

## 结论与证据

2026-10-10 07:45、07:48 两次游戏日志均显示战斗结束、地图界面恢复，然后自动打开 GauntletInventoryScreen（战利品/物品界面）。Windows 转储中的两个故障线程均为 `System.NullReferenceException`，相同调用链：

```text
TroopDesigner.SubModule.EnableSearch()
TroopDesigner.SubModule.OnApplicationTick(Single)
TaleWorlds.MountAndBlade.Module.OnApplicationTick(Single)
TaleWorlds.DotNet.Managed.ApplicationTick(Single)
```

直接故障位于 TroopDesigner 搜索功能；这两份故障栈没有进入布料求解器。安装中的明玉包、碰撞 XML 与工程 v1.1.7 一致。较早的 FMOD 74 提示不能解释这两个空引用故障。

## 本机代码核对

只读反编译安装中的 DLL：TroopDesigner `EnableSearch()` 在确认顶层界面为 GauntletInventoryScreen 后，反射取 `_dataSource`，立即访问 `IsSearchAvailable`，没有检查数据源是否为空。游戏本机 v1.4.8 的 `_dataSource` 在 `OnReady()` 中创建，`OnInitialize()` 尚未创建它，故界面已出现而数据源未就绪的窗口期会触发异常。

修复点是 TroopDesigner `EnableSearch()`：反射字段或 SPInventoryVM 尚未就绪时直接返回，不更新 `_lastScreen`，下一帧重试。无需为此回退明玉造型或关闭布料。本轮只检查日志与转储，未修改 TroopDesigner、Native 或已安装资源，未启动游戏。

详细时间线、原文件路径、哈希和两份故障线程见 [JSON 证据](inventory_crash_20261010.json)。原始 dump 留在本机 CrashDumps，未上传。CLRMD 工具和反编译缓存位于本模组 build/crash_probe/，不作为交付资源。
