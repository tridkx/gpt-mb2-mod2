# 天刀种族系列

本目录是角色工程容器，各角色作为独立骑砍 2 模块制作、安装和发布。

| 工程 | 内容 |
| --- | --- |
| [Bishui Qingluan Female Race](BishuiQingluanFemaleRace/README.md) | 碧水青鸾女性完整角色、独立种族及实时布料 |

后续角色使用独立的 `<角色Race>/`，各自保存 `input/`、`source/`、`tex/`、`tools/`、`module/<ModId>/`、`build/`、`reports/` 和 `dist/`。`source/` 与 `tex/` 相邻，模型参数和 GUID 不与其他角色共用。系列容器本身没有 `SubModule.xml`。

共用资源、布料编译和诊断工具位于工作区根 `tools/`。构建脚本向上定位工作区；打包和安装按独立模块 ID 选择工程。游戏测试由用户完成。
