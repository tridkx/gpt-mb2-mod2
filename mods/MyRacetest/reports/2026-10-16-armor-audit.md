# MyRacetest 与 diguoDiji 固有护甲检查

日期：2026-10-16。适用本机 Bannerlord v1.4.8、生成器标记0.3.1、两个模块均为v0.1.0。游戏测试由用户完成，本次未启动游戏。

## 数据与方法

使用现有 RaceTroopBuilder.Core 的 `Discovery.Scan`、`Builder.Loadouts` 与 `Builder.OriginalArmor`，从本机原版已注册 NPCCharacters 和 Items 读取装备数据，未使用替换后的装备计算基准。各战斗套汇总五个人物防具槽对头／身／臂／腿的全部贡献，多套等权平均并以 AwayFromZero 四舍五入；不计马具、平民装备、品质和特长。

原始装备套和基准见 [JSON记录](2026-10-16-original-armor-baselines.json)。

| 模块 | 兵种 | 头／身／臂／腿 | 处理 |
| --- | --- | --- | --- |
| MyRacetest | 帝国军团步兵 | 47／54／47／46 | 已匹配原版，保留 |
| MyRacetest | 帝国精英双刃枪兵 | 48／47／38／30 | 已匹配原版，保留 |
| MyRacetest | 帝国禁卫射手 | 34／34／33／24 | 已匹配原版，保留 |
| MyRacetest | 帝国军士弩手 | 37／32／41／35 | 已匹配原版，保留 |
| MyRacetest | 帝国精英具装骑兵 | 52／64／48／40 | 从无覆盖补充为原版基准 |
| diguoDiji | 帝国弩手 | 29／28／21／18 | 已匹配原版，保留 |
| diguoDiji | 帝国资深弓箭手 | 27／18／24／14 | 已匹配原版，保留 |
| diguoDiji | 帝国资深步兵 | 47／42／36／24 | 已匹配原版，保留 |
| diguoDiji | 帝国双刃枪兵 | 42／43／35／12 | 已匹配原版，保留 |
| diguoDiji | 帝国步兵 | 12／16／7／12 | 已匹配原版，保留 |
| diguoDiji | 帝国弓箭手 | 6／12／2／12 | 已匹配原版，保留 |
| diguoDiji | 帝国具装骑兵 | 52／48／32／43 | 已匹配原版，保留 |
| diguoDiji | 帝国重装骑兵 | 41／29／25／34 | 已匹配原版，保留 |

## 验证结果与安装

修改前完整备份：`../dist/MyRacetest-before-armor-20261016-092535.zip`，SHA256为 `CD7A074F0BF0EFC03FEEF335A2C48930A788096EC537BA79D4ADAE67AC644534`。

只安装了 MyRacetest 的 `ModuleData/rtb_troop_armor.xml`，安装路径为 `D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/MyRacetest/`。安装后该文件与工程副本SHA256一致：`EFC39A4F8DFEC037CC7DF698BD316EAA8BEC9771E94ADD20585B19EADD2779A7`。diguoDiji 未修改。

两模块护甲运行DLL均与现有通过离线真实方法补丁编译检查的版本一致。对启动器选中的本机模块协议进行注册读取，无重复兵种覆盖或未注册种族错误。按本机可访问模块的加载顺序应用已注册 NPCCharacters XSLT，13个目标最终种族全部匹配护甲规则，人物防具槽均为空。使用安装DLL的 `ArmorRegistry.Resolve` 逐部位读取，13个目标全部返回表中数值。结果见 [安装后记录](2026-10-16-installed-armor-runtime.txt)；暂存检查见 [暂存记录](2026-10-16-staged-armor-runtime.txt)。

本检查未创建战场 Agent、未测实际伤害，也未对任意第三方DLL的最终属性改写做完整兼容验证。原版自动战斗不会按这些固有护甲额外提高战力。用户需重启游戏、载入战役并检查精英具装骑兵的实际战场减伤。
