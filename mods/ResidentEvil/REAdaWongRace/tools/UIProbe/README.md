# 预览手腕只读诊断

适用于 REAdaWongRace v0.1.2、Native v1.4.8。用于定位游戏预览中腕部拉成细线、手掌错位，而离线回放没有相同变形的问题；不是外观修复版。

观察器每三秒扫描当前 UI，在艾达预览出现时记录实际动作集、动画通道、映射前后的绑定矩阵、最终骨骼姿态和网格名。只读取对象，不替换动作、网格或骨架，不使用 Harmony。最多记录 120 份姿态，日志上限 12 MiB。

日志位于用户文档目录的 `Mount and Blade II Bannerlord/REAdaWongRace/ui_probe_v1.jsonl`，每次启动带独立 session。模型、骨架资源、权重、纹理和 1.10 体型参数保持已验收的 v0.1.2 数据。诊断覆盖包在 `dist/REAdaWongRace_UIProbe.zip`；正式 v0.1.2 的 Mod/Source ZIP 与发布标签保留。

由用户进入物品栏或队伍预览，停留约十秒、转到能看清腕部的位置，再退出游戏；如果捏脸页也能复现，可同样停留十秒。助手随后读取日志，与最终 TPAC 骨架和离线动作对照。诊断 DLL 编译及只读检查通过不等于已在游戏捕获到数据。

退出游戏后，从原 v0.1.2 模块 ZIP 恢复 `SubModule.xml`，并删除本模块内的 `bin/Win64_Shipping_Client/REAdaWongRace.UIProbe.dll`，即可停用。只对本模块操作。

从工作区根构建：

```powershell
dotnet build mods/ResidentEvil/REAdaWongRace/tools/UIProbe/UIProbe.csproj --ignore-failed-sources -o mods/ResidentEvil/REAdaWongRace/build/ui_probe_dll
```
