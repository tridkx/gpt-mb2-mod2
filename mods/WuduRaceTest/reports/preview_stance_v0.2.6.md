# 背包与自定义角色页待机问题记录

日期：2026-10-10；候选版本 v0.2.6；Native v1.4.8。用户报告 v0.2.5 双手仍在背后，并提供 `C:/Users/DKX/Videos/Captures/Mount and Blade II Bannerlord.png`。该截图为自定义角色编辑页，男性按钮被选中。

## 当前结论与实测结果

2026-10-10 用户复测反馈：“背包预览和自定义角色页面都还是背手状态。先这样吧。记录问题，更新文档并提交。”因此 v0.2.6 两个页面的待机姿势均未通过游戏验收，问题保持未解决，按用户要求暂停处理。本次不修改运行时代码、模型、动作配置或安装资源，也不生成新版本。

此前用户反馈持武器时正常；本次没有重新验收持武器动作、性别/身材切换或其他场景。不能将本次反馈扩展为这些场景的验证结果。

## 已确认的配置遗漏

只读反编译本机 Native `TaleWorlds.MountAndBlade.GauntletUI.dll` 中 `BodyGeneratorView.Init`：创建 `facegenvisual` 时调用 `MBGlobals.GetActionSetWithSuffix(baseMonsterFromRace, IsFemale, "_facegen")`，随后在动画通道 1 设置 `act_inventory_idle_start`。它使用的路径不同于背包 `CharacterTableau` 的 `_warrior` 动作集。

本种族因此需要 `as_wdr_canglan_facegen` 和 `as_wdr_canglan_female_facegen`。v0.2.5 缺少这两个定义，前版名称修正并未覆盖用户截图的页面。缺少定义是确认的配置遗漏；补齐后的 v0.2.6 实测仍背手，说明该修正不足以解决实际问题。尚未取得游戏预览实际骨架/动作帧，不能把动作集命名认定为已证实的背手根因。

本版补齐这两个定义，显式指定 `wdr_skeleton`，分别继承原版男女 facegen 动作集。仅覆盖 `act_inventory_idle_start` 和 `act_inventory_idle`，分别引用原生 `inventory_idle_start`、`inventory_idle`，统一为已检查的背包站姿。战士、村民动作集和模型资源不变。

编辑页 `RefreshCharacterEntity` 在切换参数时会重新创建视觉对象，其数据未显式附带 ActionSet；保留本种族 Monster 已指向的男女战士默认动作集，两个默认集同样绑定自定义骨架、继承正确原生待机。最终配置检查覆盖战士、村民、编辑页共六个派生名称。

## 证据与限制

- `inventory_validation.json` 抽样最终骨架下的原版背包待机、男女原版编辑页待机；均为有限坐标。原版编辑页动作的离线图也没有明显背手，未把原生动画认定为已证实根因。
- `facegen_male_side.png`、`facegen_female_side.png` 是原版编辑页动作对照，`inventory_idle_side.png` 是本版采用的站姿对照。离线蒙皮不模拟游戏的通道合成、IK 或布料求解。
- TPAC SHA-256 保持 v0.2.5 的 `b76b79aa1117b0711d83c52c394254e6641cd432d540fa233d74c0531219e2b9`。模型、全部手部 LOD、腕部权重、眼周 UV、头发和可编辑源文件没有本轮修改。
- 原始模型目录由另一会话更新；本版继续使用已保存的输入快照。快照哈希经过检查，外部目录差异单独记录在 `release_validation.json`，不自动吸收或重复翻转 UV。
- `probe_v0.2.6.log` 在游戏初始化时记录四个战士/编辑动作集的有效性；有效性只证明可查询，不证明实际 UI 使用了该集或姿势正确。

## 已尝试方案与尚缺证据

- v0.2.5：补齐战士和村民动作集派生名称；用户反馈背手仍存在。
- v0.2.6：补齐男女 `_facegen` 动作集并明确引用原版背包待机；用户确认背包、自定义角色页均仍背手。
- 两次修正的离线检查通过，实际 UI 姿势未解决。离线预览未模拟原生动作通道合成、骨架重定向及 IK，不能代替游戏实测。
- 若以后恢复排查，需要取得两个页面实际视觉对象使用的动作集、动作通道、骨架静止帧和当前骨骼帧，再与离线数据对照。本轮不继续采样或修改，不将任何尚未验证的机制写为根因。
