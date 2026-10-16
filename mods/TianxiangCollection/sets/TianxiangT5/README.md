# 天香 T5 v1.4.2

天香 T5 三件配套装备：发容与头饰（tx5_head）、白粉长裙（tx5_body）、长袜与靴（tx5_legs）。当前交付为无布料外观版，依赖 Native、SandBoxCore、Sandbox。

## 安装与穿戴

独立版 Mod ZIP 的 TianxiangT5/ 文件夹放入游戏 Modules，在启动器启用本模块；启用天香合集时不要同时启用独立版。三件配套穿戴，手套和披肩槽留空，固定脸型不提供原生表情或捏脸。

开启作弊的战役可使用以下物品命令，也可等待商店刷新：

```text
campaign.add_item_to_player_party tx5_body
campaign.add_item_to_player_party tx5_legs
campaign.add_item_to_player_party tx5_head
```

## 当前模型与材料

- 全部四级 LOD 使用骨骼蒙皮，游戏布料停用；游戏全局开关无需更改。
- 大腿 mesh_06 / tx5_legs_06 使用不透明 tx5_skin 材质和 body_D.png。
- 衣装保留短袖和袖口，不包含左右独立长水袖布片。
- 脸、眼睛、睫毛、头发和头饰按 appearance_config.json 的同一支点放大 20%，下缘平滑过渡；18 个共享颈缝点位置、法线和权重一致。
- 原生 human 28 骨骨架，每顶点最多四权重，量化权重和为 255。

## 工程与重建

主源为 source/TianxiangT5_Rigged.blend 和同名 FBX，tex/ 与 source/ 相邻。当前运行包在 module/TianxiangT5/，制作参数在 tools/appearance_config.json，入口为 tools/build_appearance.ps1。

入口从本地 TianxiangT5/v1.4.0 标签恢复固定基线，避免重复放大；需要本机 Blender、Python、.NET、mbtool 和工作区资源工具。历史模拟代理不属于当前交付。

入口向上查找工作区根，适用于当前 sets/ 分组布局。其固定标签基线属于必要制作输入，不能据此声称只靠原始模型完成最新版冷启动重建；共用说明见[重建输入与构建缓存](../../../../docs/rebuild-and-cleanup.md)。

从工作区根检查当前交付输入：

```powershell
./tools/install_release.ps1 -Mod TianxiangT5 -Version v1.4.2 -CheckOnly
```

实际更新使用共用安装器，-PreviousVersion 应填写当前被替换交付的真实版本，保留旧 ZIP。

## 验证状态与限制

reports/appearance_validation.json 记录最终 TPAC、四级 LOD、材质贴图、Blend/FBX 和六组原生动作共 992 帧检查。appearance_comparison.png 和动作图是离线预览。

游戏测试由用户完成；头部比例、大腿显示、袖口外观、动作与远近切换仍需游戏确认。混搭、体型、武器 IK 和马体碰撞不由离线检查保证。

## 文档索引

- [更新与历史试验](CHANGELOG.md)
- [布料与材质注意事项](../../../../tools/cloth_compiler/README.md#注意事项)
- [本机历史修复资料](../../../../maintenance/README.md)
