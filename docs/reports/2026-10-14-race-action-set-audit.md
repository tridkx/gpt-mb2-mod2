# 自定义种族动作集缺失检查

日期：2026-10-14。适用版本：本机 Native v1.4.8。检查工作区 18 个种族模块、17 个独立种族 ID；其中 TianxiangRaceCollection 重复容纳天香九个独立种族，WuduRaceTest 计入测试工程。

本次只读检查 XML、已安装模块数据及本机托管程序集，不修改动作集、运行 DLL、交付包或安装状态，不启动游戏。完整逐模块、逐名称矩阵见[原始检查结果](2026-10-14-race-action-set-audit.json)。

## 主要结果

- 17 个独立种族均只定义 warrior、villager、facegen 三组男女动作集，共六项；天香合集是九组这样的注册，共 54 项。
- 全部缺少地图 `_map`、举旗地图 `_map_with_banner` 和野外对话 `_poses`。
- 另缺少领主、酒馆、守卫、儿童及 NPC 职业动作集。是否触发取决于人物所处场景和角色用途，不能将整个原版目录当作所有主角的必需清单。
- 仙剑7四个种族的六项现有动作集虽然能被 Monster 的显式 `action_set` 引用，但名称不能匹配原生按 Monster ID 生成名称的调用。这是“已注册但动态名称不可达”，与单纯没写 XML 不同。
- 已注册项的 Monster 显式引用、base_set 引用和继承链均可解析，没有发现这些引用的缺失或继承环。
- 九个已安装的相关模块（含天香合集和 WuduRaceTest）的 action_sets、monsters、skins、project.mbproj 均与工作区一致。天香九个单独模块目录未安装，游戏目录保留其合集；不能把单独目录不存在当作合集种族缺失。

## 1. 主角与英雄场景的优先缺口

| 后缀 | 核对到的本机入口 | 范围及优先级 |
| --- | --- | --- |
| `_map`、`_map_with_banner` | `MobilePartyVisual.AddCharacterToPartyIcon` | 主角地图小人，按性别与旗帜状态选择；全部缺失 |
| `_poses` | `ConversationMissionLogic` 的人物生成路径 | 野外对话场景，代码明确包含 PlayerCharacter；全部缺失 |
| `_lord` | `HeroAgentSpawnCampaignBehavior.CreateLocationCharacterForHero` | 城镇中的国王／女王、无队伍贵族和队伍领主；有这种用途时需要 |
| `_warrior_in_tavern`、`_warrior_in_aserai_tavern` | 同一英雄生成方法的 Wanderer 分支 | 自定义种族流浪者／同伴，按文化选酒馆集；不是普通主角进入酒馆就必然请求它 |
| `_guard` | `PrisonBreakCampaignBehavior` 等 | 自定义种族获救囚犯、守卫、驻军等条件路径；需按角色分配覆盖 |
| `_hideout_bandit` | `DisguiseMissionLogic` 的生成调用 | 自定义种族用于相应潜入／敌方角色时；不因主角参加据点战就自动判为主角必需 |

补齐时继承对应 Native 动作集，并指向当前种族的自定义绑定骨架。不能为了获得动作集把 BaseMonster 一概改成 human，否则其他生成参数及骨架选择也可能改变。

### 女性 `_poses` 的特殊边界

本机 Native 目录有 `as_human_poses`，没有 `as_human_female_poses`；对话代码却使用 AgentIsFemale 生成后缀名称。静态检查不能据此保证原生内部对女性的处理方式。自定义女性种族的该入口需专门验证；如使用共享 poses 基线，也应显式指向存在的 `as_human_poses`，不能虚构不存在的 female base_set。

## 2. 条件 NPC 场景缺口

以下后缀在这些工程均未定义。前四组和搬运道具的主要分支已在 SandBox／CampaignSystem 中找到调用；最后一组的三个男性搬运集仅作为 Native 目录覆盖差异列出，本次未确认其具体触发入口。

| 类别 | 缺少的后缀 |
| --- | --- |
| 村民变体、酒馆访客 | `_villager_2`、`_villager_3`、`_villager_in_tavern`、`_villager_in_aserai_tavern` |
| 儿童、反派与守卫 | `_child`、`_villain`、`_unarmed_guard`（另有前节的 `_guard`、`_hideout_bandit`） |
| 商贩、铁匠、酒馆人员 | `_seller`、`_weaponsmith`、`_barmaid`、`_tavern_keeper`、`_musician`、`_dancer`、`_beggar` |
| 要人职业与随从 | `_villager_artisan`、`_villager_merchant`、`_villager_preacher`、`_villager_gangleader`、`_villager_ruralnotable`、`_gangleader_bodyguard`、`_merchant_notary` |
| 搬运与随身道具 | `_villager_with_backpack`、`_villager_with_staff`、`_villager_carry_on_shoulder`、`_villager_carry_axe`、`_villager_carry_right_side`、`_villager_carry_front`、`_villager_carry_front_v2`、`_villager_carry_right_hand`、`_villager_carry_right_arm`、`_villager_carry_over_head`、`_villager_carry_over_head_v2` |
| 仅确认目录差异的男性搬运集 | `_worker_carry_wood_on_shoulder`、`_villager_carry_bucket_on_lefthand`、`_villager_carry_fish_buckets` |

普通独立战斗兵不需要自动补齐所有职业集；如果该种族要用于同伴、领主、守卫、要人或文化村民，则按相应生成入口扩大覆盖。注册只有性别／年龄 skin 并不能代替 `_child` 动作集。

## 3. 仙剑7的动态命名不匹配

本机命名规则为：`as_` +（Monster.BaseMonster 非空时使用它，否则使用 Monster.StringId）+ 性别后缀 + 场景后缀。FaceGen 通过 race 名查同名基础 Monster。以下四个基础 Monster 没有 BaseMonster，所以原生请求完整 ID 前缀。

| 工程 | 基础 Monster ID／原生前缀 | 实际注册前缀 | 一个缺失名称示例 |
| --- | --- | --- | --- |
| YueQingShuRace | `yqs_default`／`as_yqs_default` | `as_yqs` | `as_yqs_default_female_warrior` |
| YueQingShuOutfit2Race | `yqs2_outfit2`／`as_yqs2_outfit2` | `as_yqs2` | `as_yqs2_outfit2_female_facegen` |
| BaiMoQingRace | `bmq_default`／`as_bmq_default` | `as_bmq` | `as_bmq_default_female_villager` |
| BaiMoQingOutfit2Race | `bmq2_outfit2`／`as_bmq2_outfit2` | `as_bmq2` | `as_bmq2_outfit2_female_warrior` |

每个工程都有男女 warrior、villager、facegen 的六个动态名称缺口。直接通过 Monster.ActionSetCode 取集的路径仍能找到短名；运行组件显式使用短名的已验收预览也不能因此被追溯判为失败。但原生 `GetActionSetWithSuffix` 的 warrior／facegen、LocationCharacter 的 villager 等入口有名称不匹配风险。

若后续修复，优先新增完整前缀的动作集或兼容别名，保留旧短名、存档 race ID 与现有运行组件引用。不能只在旧短名前缀上增加 map、poses，否则原生仍查不到完整名称。

## 4. 检查方法与边界

检查 Native action_sets 中 88 个 `as_human*` 注册名称，将后缀按当前 Monster 命名规则映射到各工程，检查是否存在以及声明骨架是否与 skin 一致；同时检查显式 Monster 引用、base_set 解析与继承环。抽查的原生名称缺口不依赖网络接口版本。

除仙剑四种族外，13 个种族与原版目录比较，每个有 82 个名称未覆盖，归属 43 个后缀族；仙剑四种族因前缀不匹配，88 个原生候选名称均未覆盖。**这些数字是目录覆盖差异，不是每个角色必须补齐的数量。** 精确名单见 JSON，女性 poses 因 Native 本身没有对应名称，单独列为边界，不计入 88 个候选。

读取了本机 SandBox、SandBox.View、TaleWorlds.CampaignSystem、TaleWorlds.MountAndBlade、TaleWorlds.MountAndBlade.View 的托管代码，按具体方法核对主要调用。完整反编译源码保存在系统 TEMP，没有加入工程。JSON 中的源码字面量后缀列表仅用于辅助检索；是否确有调用以上文人工核对为准，不能把任意字符串命中当成必需依赖。

本检查未枚举所有场景资源中的动态后缀、其他第三方补丁或原生引擎内部别名；未运行游戏，因此不声称所有缺口都已经导致实机错误。已安装 XML 一致性也不等同于启动器启用了模块或所有 DLL 字节一致。

建议后续顺序：先处理仙剑命名兼容和地图／对话集，再按领主、同伴用途补充 lord 与酒馆集；只在启用 NPC 职业替换时扩展对应职业集。动作集修复与地图明暗频闪的因果验证分别验收。
