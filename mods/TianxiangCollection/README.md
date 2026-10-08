# Tianxiang Collection v1.0.0

天香八套装备合集，管理器英文名称 Tianxiang Collection，独立 ID TianxiangCollection，游戏内装备名保留中文。共 24 件装备，每套分别提供头部、身体、腿部；整套穿戴时手套和披肩槽留空。

| 套装 | 来源版本 |
| --- | --- |
| 天香 T5 | TianxiangT5 v1.4.2 |
| 纫秋为佩 | TianxiangRenqiu v1.0.1 |
| 沐风为裳 | TianxiangMufeng v1.0.3 |
| 轻梅映雪 | TianxiangQingmei v1.0.1 |
| 暮雨亭兰 | TianxiangMuyu v1.0.1 |
| 芳姿盈袖 | TianxiangFangzi v1.0.0 |
| 碎梦繁花 | TianxiangSuimeng v1.0.0 |
| 雪芷丹华 | TianxiangXuezhi v1.0.1 |

合并使用各套当前交付资源的原始字节，保留已有资源名、GUID、装备 ID、属性、材质、绑骨、布料及 LOD。没有重新绑骨或改变造型。八个 TPAC 位于同一个模块中，由同一份 items.xml 注册。保留原装备 ID 有助于延续已有装备引用，但从独立模组切换到合集的存档加载仍需游戏确认。

Mod ZIP 解压到游戏 Modules。在模组管理器只勾选 Tianxiang Collection，取消勾选上表八个独立模组；合集只依赖 Native、SandBoxCore、Sandbox，不依赖旧模块。旧工程、安装目录和交付包全部保留，不同时启用合集与独立版。

已检查八包 SHA256 与来源报告一致、资源名/GUID 无冲突、24 件装备注册与源 XML 一致、材质引用与元数据检查通过。原有几何检查由逐字节一致性继承，没有重新运行全部模型动画检查。雪芷丹华 v1.0.1 的肩臂返修已获用户游戏确认；合集作为新模块尚未游戏验证，游戏测试由你完成。

八个完整本地工程已移动到 sets/<原ModId>/，包含原始输入、源文件、贴图、专用脚本、缓存、报告、当前和历史交付包。历史 Git 标签与单套版本保留；历史报告中的旧路径按工作区 README 的映射读取。共用打包/安装器继续接受原单套 ID，并自动解析分组后的工程位置。

Source ZIP 包含八套当前可编辑 Blend/FBX、贴图、制作脚本与报告，以及合集脚本和运行包；不打包历史交付包和缓存。每套 source/ 与 tex/ 保持相邻。脚本已适配分组路径，重新制作单套仍需工作区共享工具链。合集重建执行 tools/build_collection.py --input-workspace D:/gpt-mb2-mod2，重新读取 sets/ 下的八套已检查工程；校验执行 tools/verify_collection.py。不需要重新制作模型也可直接从 module/TianxiangCollection 打包运行模块。

安装命令：工作区 tools/install_release.ps1 -Mod TianxiangCollection -Version v1.0.0。仅安装自己的合集模块，不启动游戏，不改 Native。本地 Git，不上传远程。
