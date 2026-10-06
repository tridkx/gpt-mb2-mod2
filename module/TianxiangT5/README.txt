# 天香 T5 装备模组

已安装到：`D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord\Modules\TianxiangT5`

启动器单人模式勾选 **天香 T5 · 衣装与布料**，放在 Native、SandBoxCore、Sandbox 后面。它是纯装备资源模组，不需要额外 DLL。

## 获取装备

三件装备要配套穿戴；试穿时先清空原来的披风、肩甲和手套。建议先用默认附近体型的女性角色。

| 装备 | 物品 ID | 槽位 |
| --- | --- | --- |
| 天香T5 · 白粉长裙 | `tx5_body` | 身体 |
| 天香T5 · 长袜与靴 | `tx5_legs` | 腿靴 |
| 天香T5 · 发容与头饰 | `tx5_head` | 头部 |

最快的试穿方法是在开启作弊的战役中，通过控制台分别输入：

```text
campaign.add_item_to_player_party tx5_body
campaign.add_item_to_player_party tx5_legs
campaign.add_item_to_player_party tx5_head
```

此命令及省略数量时给 1 件的行为已从本机游戏程序确认。装备设为帝国商店可出售，普通商店不会保证立即刷出。

## 已完成的制作

- 将无骨骼 FBX 适配到原版 `human_skeleton` 的 28 根骨骼；每个顶点最多 4 个影响，打包后的权重总和均为 255。
- 做成头部、身体、腿靴三个装备；头部含原模型的脸、眼、睫毛、头发和头饰，身体含原模型的裸露皮肤和双手。
- 配置覆盖原版头部、身体、手和腿，减少两套身体重叠。
- 保留原 UV 和贴图，处理头发、睫毛、花边的透明裁切，衣料 Alpha 抬底，使用中性法线和高光贴图。
- 提供 LOD0–LOD3；完整套装 LOD0 为 16,312 个三角形。
- 写入原生 `uses_cloth_simulation` 标志、顶点 Alpha 活动范围、布料材料参数，并关联游戏原版 `human_body` 碰撞胶囊。
- 修正袖后飘带误跟随腿骨、袖饰与肩肘过渡、后裙摆左右小腿权重分裂的问题。裙摆以骨盆和大腿平滑驱动。

## 布料设置及验证边界

腰部、肩部连接处、面部、鞋袜固定；衣摆最大活动距离约 7.5 厘米，袖后飘带约 11 厘米，袖边约 3 厘米，长发约 2.8 厘米。使用较高阻尼、低风力和保守惯性，降低高速动作中的摆动幅度。

这套设置是**写入游戏资产的原生布料配置**。游戏运行时的布料缓存、碰撞响应和战场表现尚未确认，不保证已经消除穿模。当前采用直接模拟，没有另外制作映射代理网格，也没有交付已烘焙的 `.tcc/.tcm`。

已完成最终 TPAC 回读检查：23 个资产的校验和与元数据一致，材质引用完整，贴图带完整 mip 链，XML 可解析，全部顶点权重和骨骼索引有效。使用原版站立、跑步、拉弓、骑乘动作进行 48 个离线姿态的数值检查；这些检查不运行游戏布料求解器。

按你的要求，游戏内试穿和布料测试由你完成。此前尝试启动 Modding Kit 未进入可验证状态；启动日志保留在 `reports` 中，不能据此判定游戏版本兼容或战场效果已通过。

优先观察：背面长发与后背、跑步时后裙摆、抬手时袖子与腋下、骑乘时裙摆与大腿/马鞍。极端体型、其他披风肩甲以及马体碰撞仍可能穿模。原版 `human_body` 胶囊不包含马体，也未确认游戏对该装备启用布料自碰撞。

## 工程文件

- `source/TianxiangT5_Rigged.blend`：可编辑的绑骨工程，贴图已打包。包含默认关闭的 Blender 布料预览副本；Blender 设置不会随 FBX 自动变成游戏布料。
- `source/TianxiangT5_Rigged.fbx`：28 骨导出文件。
- `module/TianxiangT5`：运行时模组。
- `build/spec.json`、`build/cloth_patch.json`：打包和布料参数。
- `reports/validation.json`：最终资源和离线动作检查结果。

本次构建使用本机 Blender 5.2、`D:\mb-tools` 的 TPAC 工具和 `D:\gpt-mb2-mod` 的几何/贴图辅助库。重新构建的主要步骤是 `tools/rig_model.py` → `tools/export_geometry.py` → `tools/build_package.py`。

官方说明：[布料模拟](https://moddocs.bannerlord.com/editor/resource-editors/cloth_simulation/)、[资源命名与骨骼索引](https://moddocs.bannerlord.com/asset-management/asset-types/asset_naming_conventions/)。
