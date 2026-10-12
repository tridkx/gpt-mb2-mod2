# Tianxiang Race Collection

天香完整角色种族工程的系列入口。目录名固定为用户指定的 `TianxiangRaceColletion`；系列容器本身不是游戏 Module。各套保留独立模块、资源和绑定骨架，可分别启用。

## 模组

| 独立模组 | 外观 | 种族 ID | 验收范围 |
| --- | --- | --- | --- |
| [TianxiangT5PVERace](TianxiangT5PVERace/README.md) | 天香 T5 成女校服，PVE 白粉配色 | `txt5pve` | 独立工程 |
| [TianxiangGirlT1Race](TianxiangGirlT1Race/README.md) | 少女第一套纫秋为佩 | `txgirl1` | 物品栏修复已验收；布料返修待复测 |
| [TianxiangGirlT2Race](TianxiangGirlT2Race/README.md) | 少女第二套沐风为裳 | `txgirl2` | 用户已确认验收通过 |
| [TianxiangGirlT3Race](TianxiangGirlT3Race/README.md) | 少女第 3 套轻梅映雪 | `txgirl3` | v0.1.1；站立预览裙片返修待用户复测 |
| [TianxiangGirlT4Race](TianxiangGirlT4Race/README.md) | 少女第 4 套暮雨亭兰 | `txgirl4` | v0.1.1；站立预览裙片返修待用户复测 |
| [TianxiangGirlT5Race](TianxiangGirlT5Race/README.md) | 少女第 5 套芳姿盈袖 | `txgirl5` | v0.1.1；站立预览裙片返修待用户复测 |
| [TianxiangGirlT6Race](TianxiangGirlT6Race/README.md) | 少女第 6 套碎梦繁花 | `txgirl6` | v0.1.1；站立预览裙片返修待用户复测 |
| [TianxiangGirlT7Race](TianxiangGirlT7Race/README.md) | 少女第 7 套雪芷丹华 | `txgirl7` | v0.1.1；站立预览裙片返修待用户复测 |
| [TianxiangGirlT8Race](TianxiangGirlT8Race/README.md) | 少女第 8 套臻姿凤仪，PVP | `txgirl8` | v0.1.1；站立预览裙片返修待用户复测 |

## 少女八套制作范围与使用

源输入为 `D:/dsh-tiandao/天香少女校服8套/`。第一、二套保留各自已有功能；第 3–8 套提供独立完整人物种族资源，第八套仅使用 PVP 配色。后六套不添加测试兵种，不覆盖原版兵种、招募池或升级树。配置人物或兵种时使用 [Race Troop Builder](../RaceTroopBuilder/README.md)，选择对应种族 ID；完整身体自带衣服，避免叠加原版防具。

后六套保留源固定脸、衣服、头发、双手与身体比例；v0.1.1 为站立预览交叉位置补了局部横向裙片间隙，身体和绑定不变。服装使用骨骼蒙皮，提供四级 LOD 和人物预览适配，不提供独立布料飘动、捏脸形变、表情或动态手指握持。各套的离线证据和游戏验收要点集中在对应 README。

## 目录与交付

每套分别维护 `input/`、`source/`、`tex/`、`tools/`、`module/<ModId>/`、`build/`、`reports/` 和 `dist/`。`source/` 与 `tex/` 保持相邻。`dist/` 下的 Mod ZIP 可解压到游戏 `Modules`，Source ZIP 保存可编辑模型、贴图和构建工具；共用工具恢复方式见各套 README。

制作、依赖和安装命令见各模组 README。源文件使用本地 Git；游戏验收由用户完成。与天香装备合集的用途区分见[工作区入口](../../README.md)。
