# CLI 与工程格式

## 命令

在发布包根目录运行。路径有空格时按当前 shell 的规则加引号。`--mods` 可重复；命令只接受列出的参数，拼写错误会拒绝执行。

```powershell
.\rtb.cmd scan
.\rtb.cmd scan --game "D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord" --mods "D:\gpt-mb2-mod2\mods"
.\rtb.cmd catalog --kind races
.\rtb.cmd catalog --kind troops --filter 帝国 --lang zh-CN
.\rtb.cmd catalog --kind items --filter sword --lang en
.\rtb.cmd troop --id imperial_recruit
.\rtb.cmd new --out my-troops.json --id MyRaceTroops --name "My Race Troops"
.\rtb.cmd configure --project my-troops.json --rule examples/recruit-weapons.rule.json
.\rtb.cmd validate --project my-troops.json
.\rtb.cmd preview --project my-troops.json
.\rtb.cmd build --project my-troops.json --out output/release-001
.\rtb.cmd package --report output/release-001/MyRaceTroops.validation.json --out output/MyRaceTroops-v0.1.0.zip
.\rtb.cmd install --report output/release-001/MyRaceTroops.validation.json
```

源码入口等价于 `dotnet run --project source/Cli/RaceTroopBuilder.Cli.csproj -- <命令与参数>`。

| 命令 | 作用 |
| --- | --- |
| `scan` | 游戏版本、目录数量、种族、模块依赖及来源歧义 |
| `catalog --kind troops/items/races` | 双语搜索目录；名称使用 `--lang zh-CN/en`，配置使用稳定 ID |
| `troop --id ID` | 原始 XML、升级目标、展开后的装备套 |
| `new --out FILE` | 新建空工程，不覆盖已有文件 |
| `configure --project FILE --rule FILE [--index N]` | 追加或替换零起始索引规则；全部规则通过检查才写回 |
| `validate --project FILE` | 检查配置、引用、种族性别、依赖与升级图 |
| `preview --project FILE` | 报告、beforeXml/afterXml 与固有护甲继承／覆盖信息 |
| `build --project FILE --out ROOT` | 生成 ROOT/ModuleId、检查报告与工程快照，不覆盖已有构建 |
| `package --report FILE --out ZIP` | 检查文件哈希后打包模块与检查报告 |
| `install --report FILE [--game PATH] [--backups PATH]` | 校验依赖与模块，备份并安装；不启用启动器勾选、不启动游戏 |

`scan/catalog/troop/new/configure/validate/preview/build` 支持 `--game` 和重复的 `--mods` 覆盖来源。`--game` 优先于工程路径，然后使用 `BANNERLORD_GAME_ROOT` 和常见 Steam 库位置。未配置 Mod 来源时优先查找当前工作目录所属工作区的 `mods/`，其次查找可执行文件所属工作区，再使用当前目录下的 `mods/`。自动探测未找到游戏时应显式指定目录。

## 名称语言

`catalog --kind troops/items` 返回 `nameEn`、`nameZh`、`nameKey` 和当前 `displayName`；已有 `name` 字段继续表示原版英文回退名。中文缺失时回退英文，`--filter` 同时匹配两种名称和 ID。`troop` 同样返回双语字段。工程的 `displayLanguage` 默认为 `zh-CN`，也可用 `en`；语言只影响工具展示，不改变兵种 ID 或输出 XML 的原版语言键。GUI 操作标签仍为中文。

## 工程格式 v1

主要规范为 [project.schema.json](../schemas/project.schema.json)。源码默认值允许空工程保存；构建要求至少一条有效规则。未知 JSON 字段拒绝读取，不静默忽略拼写错误。

```json
{
  "schemaVersion": 1,
  "displayLanguage": "zh-CN",
  "moduleId": "MyRaceTroops",
  "moduleName": "My Race Troops",
  "version": "v0.1.0",
  "gameRoot": null,
  "modRoots": [],
  "rules": [{
    "rootIds": ["imperial_recruit"],
    "raceModule": "YueQingShuRace",
    "raceId": "yqs_default",
    "isFemale": true,
    "age": 25,
    "faceMode": "fixed",
    "stripArmor": true
  }]
}
```

规则可使用 `armor` 配置固有护甲继承或覆盖，规范和运行组件接入方式见 [固有护甲接口](armor.md)。完整覆盖格式示例见 [armor-override.json](../examples/armor-override.json)，其中种族模块和 ID 是需要替换的占位符。

路径字符串若为相对路径，按 JSON 文件所在目录解析。空 `modRoots` 使用默认扫描根。CLI 覆盖参数不会更改原工程，`configure` 成功时会保存实际来源；构建的工程快照保存实际来源。

规则的 `troopIds` 精确选择节点，`rootIds` 包含所选节点及其全部可达升级节点，`culture` 选择当前文化所有士兵 / 雇佣兵。三者取并集；不同规则不可覆盖同一兵种。省略或 null 的 `isFemale/age` 保留原版；`faceMode=preserve` 保留脸参数，`fixed` 使用本机完整身体基线的零键、年龄和固定体重体型。新种族是否支持该脸策略需实机确认。

`name` 可选，用于替换显示名；批量规则将所有目标改成该名字，通常应省略。文化、等级与升级边没有编辑字段，始终来自原版目标节点。技能可通过可选的 `skills` 字典覆盖。

`battleLoadouts/civilianLoadouts` 省略或 null 表示保留该类型的原版装备；提供列表表示完整替换该类型。战斗列表不能为空，平民列表可以为空。空槽应删除字典键，而不是填写不存在的物品 ID。物品 ID 接受裸 ID 或 `Item.ID`。

```json
"battleLoadouts": [
  { "slots": { "Item0": "empire_sword_1_t2", "Item1": "peasant_2haxe_1_t1" } },
  { "slots": { "Item0": "empire_sword_2_t3", "Item1": "peasant_maul_t1" } }
]
```

合法槽为 `Item0`、`Item1`、`Item2`、`Item3`、`Head`、`Cape`、`Body`、`Leg`、`Gloves`、`Horse`、`HorseHarness`。`stripArmor=true` 从两类全部装备套中删除 Head/Cape/Body/Leg/Gloves，包括引用原版 EquipmentSet 的平民装备；新列表也遵循该清除设置。

## 技能配置

规则可添加 `"skills": { "OneHanded": 180, "Athletics": 150, "Riding": 0 }`。支持 OneHanded、TwoHanded、Polearm、Bow、Crossbow、Throwing、Athletics、Riding；值为 0～2147483647 的整数（存储范围，不代表平衡建议）。未知 ID、负数、小数拒绝读取或检查。省略、null、空字典均保留原版技能；未填写的键保持原节点不变，0 为明确覆盖。旧工程无需迁移，schemaVersion 仍为 1。

GUI 显示各项原版值，可应用到单节点或批量范围。空白不新增覆盖，并保留各目标已有的其他技能配置；“恢复原版”明确删除该范围对应的技能覆盖。切换语言不会丢失未应用的技能草稿。JSON 使用稳定的英文技能 ID；修改对比返回实际 beforeXml/afterXml。

## 输出与错误

标准输出为 JSON。检查报告包括 `status`、`issues`、`targets`、`loadOrder`、`gameVersion`、`transformChecks` 和构建文件哈希。每条问题包含 `severity/code/message/subject`，AI 应按 `code` 分支，而不是匹配中文文本。

常用错误码：`skill_id`、`skill_value`、`race_missing`、`skin_missing`、`race_collision`、`duplicate_module`、`troop_missing`、`rule_overlap`、`upgrade_cycle`、`upgrade_missing`、`item_missing`、`item_slot`、`slot`、`dependency`、`dependency_dll_missing`、`game_version`。随机弹药与无关合集重复为 warning，不阻止构建。

构建模块只注册 `NPCCharacters`，内容为同名空 XML 加 XSLT 精确替换，启动器依赖按拓扑顺序声明。检查报告、工程快照位于模块之外；包中包含模块与报告，不复制任何种族资源。种族模块的哈希仅用于安装一致性验证。
