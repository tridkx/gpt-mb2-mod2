# Genshin Race Collection

原神完整角色种族工程容器。每个角色保留独立模块 ID、原始输入、可编辑源文件、参数、检查报告和交付目录；本目录本身不是可安装的游戏模块。

| 工程 | 模块 ID | 范围 |
| --- | --- | --- |
| [艾梅莉埃](EmilieRace/README.md) | `EmilieRace` | 固定外观种族；裙摆普通蒙皮，帽后长饰及背后飘带布料 |

新角色放在 `<Character>Race/`，使用自己的 `mod.json`、`tools/`、`module/<ModId>/`、`build/` 和 `dist/`。`source/` 与 `tex/` 保持相邻，不共用角色骨架、资源名、GUID 或布料参数。共用依赖位于工作区根 `tools/`，脚本向上定位工作区，不依赖固定目录深度。

构建、依赖和使用方法见各角色 README；[工作区入口](../../README.md)。
