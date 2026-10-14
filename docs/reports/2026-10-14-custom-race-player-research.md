# 自定义种族主角：地图明暗频闪、读档与装备隐形调研

日期：2026-10-14。适用范围：本机 Native v1.4.8 的托管代码与当前工作区抽样工程；公开资料作为交叉参考。本文是调研记录，不代表修复或实机验收。本次未启动游戏、修改模组、安装模块或更改存档。

## 结论与证据等级

| 问题 | 结论 | 证据边界 |
| --- | --- | --- |
| 大地图画面明暗交替 | 根因未确定；需要地图渲染 A/B 验证 | 用户报告几乎所有自定义种族主角均出现，画面上方忽明忽暗，无黑屏、闪光或拉伸 |
| 读档变回人类 | 本机加载路径确实用原始角色模板覆盖运行时 Race；可通过额外存档数据恢复 | 已核对本机代码，另有公开项目独立修复案例 |
| 装备隐形且保留属性 | 有可行实现路线：不可见 CosmeticItem，或按人物过滤防具渲染 | 已确认外观与属性的分离接口；战场原生路径、全部界面与身体遮盖仍需验证 |

## 1. 大地图明暗频闪

### 已确认的地图创建路径

`SandBox.View.Map.Visuals.MobilePartyVisual.AddCharacterToPartyIcon` 使用当前人物 Race 找 Monster，按性别及是否举旗请求 `_map` 或 `_map_with_banner` 动作集，传入 Race、Monster、0.3 的地图比例和 `HasClippingPlane(true)` 创建 AgentVisuals。它不是物品栏 CharacterTableau。

`ActionSetCode.GenerateActionSetNameWithSuffix` 以 Monster.BaseMonster（存在时）或 StringId 生成动作集名称。`MBGlobals.GetActionSet` 对无效动作集抛出 `Invalid action set code`，没有自动回退 human 的分支。

抽样检查 ModernGirlRace、BoRuRace、YueQingShuRace 的工作区 `action_sets.xml`，仅见 warrior、villager、facegen 及对应女性集，未见 map 系列。对于这些没有 human BaseMonster 的基础 Monster，地图所需注册不完整。安装目录、实际加载集合及其他补丁是否补齐仍需核对。**这是确定的配置缺口，不是已确认的明暗频闪根因**；其直接行为更接近创建失败或错误日志。

后续[全工作区动作集检查](2026-10-14-race-action-set-audit.md)核对了 18 个模块，发现对话 poses 等场景也未覆盖，且仙剑7四种族有动态前缀不匹配；已安装的相关 XML 与工程一致。具体缺口、触发范围与女性 poses 边界集中在该检查报告。

候选补齐方式：给实际解析名称注册男女 `_map`、`_map_with_banner`，分别继承当前 Native 中对应的 human 地图集，但指向本角色的绑定骨架。名称必须按实际 Monster 解析，不能照抄其他模型的 ID。只补 warrior 或 facegen 不覆盖地图路径。

抽样 UI 修复组件已明确跳过 MapScreen，并限定预览字段；当前源码不支持“UI 每隔 0.25 秒重建地图小人”这一结论。仍应核对实际安装 DLL 是否一致。原生地图刷新会先 ResetPartyIcon 再重建；只有观测到持续置脏或重复创建，才可归因为重建循环。

### 与用户症状相符的待验证方向

以下是排查假设，尚无运行记录证明其因果关系：

- 地图人物的动态阴影、异常动画包围盒或缩放影响地图渲染。
- 镜头距离变化触发 LOD 切换，远级网格、权重或材质行为异常。
- 透明、Alpha test、重叠表面或原版防具与完整身体叠加。
- 地图图标被其他组件反复置脏、刷新或更改状态。
- 若隐藏自定义人物后仍发生，则扩大到地图光照、后处理、抗锯齿、显示设置及共享补丁；不能仅凭“使用自定义种族时出现”断定模型自身有错。

官方说明确认网格按 LOD 分组且随距离切换，材质包含 shader、纹理与渲染标志；这些说明支持检查对象，不证明某项就是本次故障原因。[网格说明](https://moddocs.bannerlord.com/asset-management/asset-types/meshes/)、[材质说明](https://moddocs.bannerlord.com/asset-management/asset-types/materials/)。

### 建议的最小实机对照

用户运行游戏，固定地点、镜头、天气与时间，先保留完整基线。各对照只改变一个因素，再恢复基线：

| 对照 | 结果如何解释 |
| --- | --- |
| 保持主角 Race 与属性，仅暂时隐藏主角地图图标 | 频闪消失说明与图标渲染有关；不能进一步直接认定阴影 |
| 仅关闭动态图影，或诊断组件仅禁用目标图标投影 | 消失则优先查阴影路径、骨架与包围盒；属于定位，不是最终修复 |
| 图标改用不透明简单材质；另做固定 LOD 对照 | 分别隔离材质与 LOD；测试副本不覆盖原始资源 |
| 脱去防具，分别徒步／骑马、举旗／未举旗观察 | 区分防具叠加、坐骑和两组地图动作集 |
| 记录图标创建／销毁、置脏频率及实体状态 | 验证是否存在重复重建，避免按固定周期盲目刷新 |

诊断数据应含 Race 名称与索引、Monster、动作集及骨架名称、最终 Scale、实体 Frame、动画通道、网格／LOD、包围盒和创建计数。若简单图标稳定，可以评估专用轻量地图外观；保留主角真实种族与战场身体，不能为地图显示把人物数据改回 human。

## 2. 读档变回原版人类

### 本机机制

`BasicCharacterObject.Race` 为普通 `int` 属性，没有直接 Saveable 标记。`CharacterObject` 保存 `_originCharacter`。加载路径 `InitializeHeroCharacterOnAfterLoad` 调用 `InitializeHeroBasicCharacterOnAfterLoad(_originCharacter)`，后者明确执行 `Race = originCharacter.Race`。

因此，捏脸或控制台在运行时改成自定义种族，而原始模板仍是 human 的主角，读档时会被模板种族覆盖。`UpdatePlayerCharacterBodyProperties` 会写当前 Race，但该写入本身没有解决以上加载覆盖。XML 模板原本就是自定义种族的英雄不一定表现为变回 human；不能把问题泛化为所有自定义种族人物都会丢失。

### 可行修复设计

1. 用独立 CampaignBehavior 在 `SyncData` 中保存目标英雄稳定标识和种族名称；主角专用功能可以只保存主角，不扩展到所有英雄。
2. 新建角色、确认种族更改、保存前更新记录；加载后先恢复，再采集，避免先把已经重置的 human 写回记录。
3. 用名称解析当前 Race 索引，不只存整数。模块加载顺序变化可能改变索引；种族不存在时记录缺失并停止恢复。
4. 核对加载时序，确保恢复早于目标场景首次创建；若会话事件太晚，使用更早且已加载完保存数据的入口。恢复后只刷新必要的地图／预览对象，不在 Tick 中不断强制赋值。
5. 同一进程加载不同存档时清理前一会话缓存。旧存档未保存种族记录时，不能自动推断原种族，应让用户选择一次后建立记录。

公开 TAOM 项目已有同类持久化实现，可参考事件接线和加载顺序；本机建议直接保存名称，或保存索引并附名称表。[问题记录](https://github.com/haterade22/TAOM/issues/13)、[持久化服务源码](https://github.com/haterade22/TAOM/blob/bannerlord-1.4.5/Main/Features/HeroRace/RacePersistenceService.cs)、[行为源码](https://github.com/haterade22/TAOM/blob/bannerlord-1.4.5/Main/Features/HeroRace/RacePersistenceBehavior.cs)。

验收应覆盖：新建角色保存／重启读档、游戏内读档、连续载入不同存档、种族切换后再次保存，以及模块加载顺序变化。存档列表里的头像预览属于独立 BasicCharacterTableau，头像表现不能代替加载后实际 Hero.Race 检查。

## 3. 自定义种族主角穿戴装备隐形

这里按“隐藏头盔、身体甲、手套、鞋靴、披风，同时保留装备及属性”调研。武器、盾牌、坐骑默认继续显示；若要求隐藏，也需另查其独立渲染与交互路径。

### 优先评估：不可见 CosmeticItem

`EquipmentElement` 同时持有原 Item、ItemModifier 与 CosmeticItem。官方 API 公开了该字段及构造参数。[EquipmentElement API](https://apidoc.bannerlord.com/v/1.3.4/struct_tale_worlds_1_1_core_1_1_equipment_element.html)。

本机 `AgentVisuals.AddArmorMultiMeshesToAgentEntity` 在防具槽中使用 `CosmeticItem ?? Item` 选外观；护甲计算 `GetModifiedHeadArmor`／`GetModifiedBodyArmor` 等读取原 Item 和 ItemModifier。`MBEquipmentMissionExtensions.GetSkinMeshesMask` 有外观物品时优先使用其 MeshesMask，头发／胡须遮盖也读取 CosmeticItem。

可为五个槽建立正确类型的不可见占位外观，仅对目标种族主角使用。保留原装备和词缀，避免修改共享 ItemObject 影响所有穿戴者。占位资源应有效且各使用 LOD 均不可见，不用不存在的 mesh 名称。

必须处理的边界：

- 设 `CosmeticItem = null` 会回退原外观，不能表示隐藏。
- 在本机它没有保存字段标记，读档后需重新应用；优先在渲染／生成副本上应用，避免污染背包与持久装备。
- BodyMeshType、BodyDeformType 等仍有读取原物品的路径，不能认为外观占位自动解决所有身体遮盖。完整身体必须保持可见，手、头、发及腿不能被原装备生成参数裁掉。
- 地图和 UI 的 AgentVisuals 路径已读到相关代码；战场有原生边界，仍需核对实际装备生成与刷新入口，再做实机验证。
- 换装、切换战斗／平民装备、进入城镇和重新生成 Agent 时均需重新应用；使用幂等事件入口，避免每帧重建。

### 其他方案

| 方案 | 适用范围与取舍 |
| --- | --- |
| 在目标人物的防具生成入口跳过网格，同时修正 SkinGenerationParams | 可以保留原装备属性；需覆盖地图、UI 和战场，维护成本较高 |
| 独立制作带护甲属性的隐形装备 | 资源路线直观，但只能隐藏这些专用物品，不能让任意原版防具自动隐形 |
| 不穿防具，改用种族固有护甲 | 可保留完整角色外观；不等同于“所穿装备仍提供属性” |

只把护甲材质设为透明，可能仍触发身体隐藏、阴影或其他渲染行为；不作为完整解决方案。直接删除实际装备会失去装备提供的护甲与重量，也不符合保留属性的目标。

验收比较隐藏前后：原 Item／ItemModifier、护甲各部位、重量及移动属性保持一致；检查地图、物品栏、队伍／百科、战场、城镇和平民装，覆盖换装与保存／加载。确认只影响目标主角，其他人穿同一物品仍正常显示。

## 本机证据与后续顺序

游戏根目录：`D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/`，Native SubModule 声明 v1.4.8。托管 DLL 的通用 FileVersion 1.0.0.0 不能当作游戏版本。

| 检查程序集 | SHA256 |
| --- | --- |
| bin/Win64_Shipping_Client/TaleWorlds.Core.dll | 3E5CECE8CA42FAF3FDDE27632519ED2A6F86D1EC6D1A742867729F00001689BF |
| bin/Win64_Shipping_Client/TaleWorlds.CampaignSystem.dll | 1F8E33E2ED73E6EC653D7629180AFB70649DDC6E5BD1657A802A264EFDA1C3AE |
| Modules/Sandbox/bin/Win64_Shipping_Client/SandBox.View.dll | C7360E71DA06799A0CB6C00C4A0CFAB5877621197BA25101433AC28654D169E2 |

通过 ilspycmd 读取本机上述类型与 Native 的 AgentVisuals，实现细节以对应方法为依据。反编译临时文件放系统 TEMP，不把游戏程序集或完整反编译源码加入工程。跨程序集未解析类型可能产生反编译警告，因此这里只采用已明确读到的赋值、分支与调用，不推断原生引擎内部实现。

后续实施顺序：先做种族名称持久化；选择一个已可用种族补齐地图注册并进行明暗频闪对照；最后接入目标主角防具外观过滤，分别验收属性、身体遮盖和各显示入口。频闪根因未查明前，不批量改写所有模型或材质。
