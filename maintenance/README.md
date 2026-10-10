# 本机历史修复资料

此目录保存本机修复脚本、报告与原文件备份。执行写入需有本次任务授权；重新安装装备包不会自动执行这些修复。

## 本机启动修复（2026-10-06）

加载画面崩溃的日志在读取 `jingrenou` 身体模型时中断，当前已启用的资源包中找不到该模型。崩溃转储为 `TaleWorlds.Native.dll + 0x725eff` 的空引用读取；10 月 2 日也有相同位置的崩溃记录。

按你的许可，已清理原版 `Native/ModuleData/skins.xml` 中的镜人偶种族，以及 `action_sets.xml` 中的镜人偶动作集。只移除了 `JJRO_BEGIN` / `JJRO_END` 标记之间的内容，其他配置经对比保持一致。原文件、清理后的副本和校验记录位于 `backups/jingrenou_cleanup_20261006`，操作报告位于 `reports/launch_repair.json`，并纳入本地 Git。

清理后，你已能进入游戏并反馈装备显示问题；该显示问题由上面的 v1.1.1 材质修复处理。这项启动修复针对本机旧模组残留，单独重新解压天香压缩包不会执行镜人偶配置清理。

已安装到：`D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord\Modules\TianxiangT5`

历史段落中的安装位置与显示名仅表示当时状态，当前装备说明见 [天香 T5](../mods/TianxiangCollection/sets/TianxiangT5/README.md)。
