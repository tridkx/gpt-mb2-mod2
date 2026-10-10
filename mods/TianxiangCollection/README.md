# Tianxiang Collection v1.0.0

## 内容

天香八套装备合集，管理器英文名称 Tianxiang Collection，独立 ID TianxiangCollection，游戏内装备名保留中文。共 24 件装备，每套分别提供头部、身体、腿部；整套穿戴时手套和披肩槽留空。

| 套装 | 来源版本 |
| --- | --- |
| 天香 T5 | [TianxiangT5 v1.4.2](sets/TianxiangT5/README.md) |
| 纫秋为佩 | [TianxiangRenqiu v1.0.1](sets/TianxiangRenqiu/README.md) |
| 沐风为裳 | [TianxiangMufeng v1.0.3](sets/TianxiangMufeng/README.md) |
| 轻梅映雪 | [TianxiangQingmei v1.0.1](sets/TianxiangQingmei/README.md) |
| 暮雨亭兰 | [TianxiangMuyu v1.0.1](sets/TianxiangMuyu/README.md) |
| 芳姿盈袖 | [TianxiangFangzi v1.0.0](sets/TianxiangFangzi/README.md) |
| 碎梦繁花 | [TianxiangSuimeng v1.0.0](sets/TianxiangSuimeng/README.md) |
| 雪芷丹华 | [TianxiangXuezhi v1.0.1](sets/TianxiangXuezhi/README.md) |

运行包使用各套当前交付资源的原始字节，保留已有资源名、GUID、装备 ID、属性、材质、绑骨、布料及 LOD。八个 TPAC 位于同一个模块中，由同一份 items.xml 注册。保留原装备 ID 有助于延续已有装备引用，但从独立模组切换到合集的存档加载仍需游戏确认。

## 安装

Mod ZIP 解压到游戏 Modules。在模组管理器只勾选 Tianxiang Collection，取消勾选上表八个独立模组；合集只依赖 Native、SandBoxCore、Sandbox，不依赖旧模块。旧工程、安装目录和交付包全部保留，不同时启用合集与独立版。

## 验证范围

合集检查记录见 [release_validation.json](reports/release_validation.json)。

已检查八包 SHA256 与来源报告一致、资源名/GUID 无冲突、24 件装备注册与源 XML 一致、材质引用与元数据检查通过。原有几何检查由逐字节一致性继承，没有重新运行全部模型动画检查。雪芷丹华 v1.0.1 的肩臂返修已获用户游戏确认；合集作为新模块尚未游戏验证，游戏测试由你完成。

## 工程与重建

八个单套工程在 sets/<原ModId>/，各自保存 input/、source/、tex/、tools/、build/、reports/ 和 dist/。共用打包与安装入口接受原单套 ID。历史路径对照见 [工作区历史路径](../../docs/historical-paths.md)。

Source ZIP 包含八套当前可编辑 Blend/FBX、贴图、制作脚本与报告，以及合集脚本和运行包；不打包历史交付包和缓存。每套 source/ 与 tex/ 保持相邻。重新制作单套需工作区共享工具链，并核对该套 README 中的入口限制。在合集工程目录执行 `python tools/build_collection.py --input-workspace D:/gpt-mb2-mod2`，重新读取 sets/ 下的八套已检查工程；校验执行 `python tools/verify_collection.py`。不需要重新制作模型也可直接从 module/TianxiangCollection 打包运行模块。

## 交付

安装条件检查：在工作区根执行 `./tools/install_release.ps1 -Mod TianxiangCollection -Version v1.0.0 -CheckOnly`。仅安装自己的合集模块，不启动游戏，不改 Native。本地 Git，不上传远程。

## 历史记录

合集目录整理见 [工作区更新日志](../../docs/CHANGELOG.md)，单套版本变化见对应工程 CHANGELOG。
