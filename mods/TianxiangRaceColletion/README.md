# Tianxiang Race Collection

天香完整角色种族工程的系列入口。目录名固定为用户指定的 `TianxiangRaceColletion`；系列容器本身不是游戏 Module。

## 模组

| 独立模组 | 外观 | 种族 ID |
| --- | --- | --- |
| [TianxiangT5PVERace](TianxiangT5PVERace/README.md) | 天香 T5 成女校服，PVE 白粉配色 | `txt5pve` |

## 目录约定

每个后续模型在本目录下新建独立 `<ModId>/`，分别维护 `input/`、`source/`、`tex/`、`tools/`、`module/<ModId>/`、`build/`、`reports/` 和 `dist/`。模型可以分别启用和交付，资源 ID、GUID、骨架和参数不能相互覆盖。`source/` 与 `tex/` 保持相邻。

制作、依赖和安装命令见各模组 README。源文件使用本地 Git；游戏验收由用户完成。与天香装备合集的用途区分见[工作区入口](../../README.md)。
