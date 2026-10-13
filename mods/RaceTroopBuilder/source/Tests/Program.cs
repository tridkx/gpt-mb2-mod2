using System.IO.Compression;
using System.Xml.Linq;
using System.Xml.Xsl;
using RaceTroopBuilder.Core;

var output = Path.GetFullPath(args.FirstOrDefault() ?? "test-results");
Directory.CreateDirectory(output);
var fixture = Path.Combine(output, "fixture-" + Guid.NewGuid().ToString("N"));
var game = Path.Combine(fixture, "game"); var mods = Path.Combine(fixture, "mods");
var results = new List<object>(); var failures = 0;
void Assert(bool condition, string message) { if (!condition) throw new Exception(message); }
void Throws(Action action, string message)
{ try { action(); } catch (Exception e) when (e is IOException or InvalidDataException or ArgumentException) { return; } throw new Exception(message); }
void Test(string name, Action action)
{
    try { action(); results.Add(new { name, status = "pass" }); }
    catch (Exception e) { failures++; results.Add(new { name, status = "fail", message = e.Message }); }
}
void Write(string path, string content) { Directory.CreateDirectory(Path.GetDirectoryName(path)!); File.WriteAllText(path, content); }
void Module(string path, string id, string dependencies, string xmls = "") => Write(Path.Combine(path, "SubModule.xml"),
    $"<Module><Id value='{id}'/><Name value='{id}'/><Version value='v1.4.8'/><DependedModules>{dependencies}</DependedModules><SubModules/><Xmls>{xmls}</Xmls></Module>");
string Entry(string kind, string path) => $"<XmlNode><XmlName id='{kind}' path='{path}'/><IncludedGameTypes><GameType value='Campaign'/></IncludedGameTypes></XmlNode>";
foreach (var id in new[] { "Native", "SandBoxCore", "Sandbox", "StoryMode" })
    Module(Path.Combine(game, "Modules", id), id, id == "Native" ? "" : "<DependedModule Id='Native'/>");
var corePath = Path.Combine(game, "Modules", "SandBoxCore");
Module(corePath, "SandBoxCore", "<DependedModule Id='Native'/>", Entry("Items", "items") + Entry("NPCCharacters", "troops") + Entry("EquipmentRosters", "sets"));
Write(Path.Combine(corePath, "ModuleData", "items", "items.xml"), "<Items>" + string.Join("", new[]
{
    ("sword1", "OneHandedWeapon"), ("sword2", "OneHandedWeapon"), ("twohand1", "TwoHandedWeapon"), ("twohand2", "TwoHandedWeapon"),
    ("bow", "Bow"), ("arrows", "Arrows"), ("cape", "Cape"), ("cape2", "Cape"), ("armor", "BodyArmor"), ("horse", "Horse"), ("harness", "HorseHarness")
}.Select(x => $"<Item id='{x.Item1}' name='{{=item}}{x.Item1}' Type='{x.Item2}'>" +
    (x.Item1 == "cape2" ? "<ItemComponent><Armor head_armor='2' body_armor='3' arm_armor='4' leg_armor='5'/></ItemComponent>" :
     x.Item1 == "armor" ? "<ItemComponent><Armor body_armor='20' arm_armor='10' leg_armor='8'/></ItemComponent>" : "") + "</Item>")) + "</Items>");
Write(Path.Combine(corePath, "ModuleData", "sets.xml"), "<EquipmentRosters><EquipmentRoster id='civilian_set'><EquipmentSet equipmentType='Civilian'><Equipment slot='Body' id='Item.armor'/><Equipment slot='Item0' id='Item.sword1'/></EquipmentSet></EquipmentRoster></EquipmentRosters>");
string Troop(string id, string next = "") => """
<NPCCharacter id="__ID__" name="{=name___ID__}__ID__" occupation="Soldier" culture="Culture.empire" level="6" is_basic_troop="__BASIC__">
  <face><face_key_template value="BodyProperty.human"/></face><skills><!--preserved skill comment--><skill id="Athletics" value="20"/><skill id="Bow" value="5"/></skills>
  <upgrade_targets>__UPGRADE__</upgrade_targets>
  <Equipments><EquipmentRoster><equipment slot="Item0" id="Item.sword1"/><equipment slot="Item1" id="Item.twohand1"/><equipment slot="Cape" id="Item.cape"/><equipment slot="Cape" id="Item.cape2"/></EquipmentRoster>
  <EquipmentRoster><equipment slot="Item0" id="Item.sword2"/><equipment slot="Item1" id="Item.twohand2"/><equipment slot="Body" id="Item.armor"/></EquipmentRoster>
  <EquipmentSet id="civilian_set" equipmentType="Civilian"/></Equipments>
</NPCCharacter>
""".Replace("__ID__", id).Replace("__BASIC__", id == "recruit" ? "true" : "false")
    .Replace("__UPGRADE__", next.Length > 0 ? "<upgrade_target id='NPCCharacter." + next + "'/>" : "");
Write(Path.Combine(corePath, "ModuleData", "troops.xml"), "<NPCCharacters>" + Troop("recruit", "veteran") + Troop("veteran", "elite") + Troop("elite") +
    "<NPCCharacter id='hero' occupation='Lord' is_hero='true' name='{=hero}Hero'><skills></skills></NPCCharacter></NPCCharacters>");
var troopFile = Path.Combine(corePath, "ModuleData", "troops.xml");
var troopDocument = XDocument.Load(troopFile);
troopDocument.Root!.Add(XElement.Parse(Troop("mercenary", "mercenary_elite").Replace("occupation=\"Soldier\"", "occupation=\"Mercenary\"")),
    XElement.Parse(Troop("mercenary_elite").Replace("occupation=\"Soldier\"", "occupation=\"Mercenary\"")),
    new XElement("NPCCharacter", new XAttribute("id", "obsolete_mercenary"), new XAttribute("occupation", "Mercenary"), new XAttribute("is_obsolete", "true")),
    new XElement("NPCCharacter", new XAttribute("id", "hidden_mercenary"), new XAttribute("occupation", "Mercenary"), new XAttribute("is_hidden_encyclopedia", "true")),
    new XElement("NPCCharacter", new XAttribute("id", "hero_mercenary"), new XAttribute("occupation", "Mercenary"), new XAttribute("is_hero", "true")));
troopDocument.Save(troopFile);
var racePath = Path.Combine(mods, "Series", "RaceOne", "module", "RaceOne");
Module(racePath, "RaceOne", "<DependedModule Id='Sandbox'/>");
Write(Path.Combine(racePath, "ModuleData", "project.mbproj"), "<base><file id='soln_skins' name='ModuleData/races.xml'/></base>");
Write(Path.Combine(racePath, "ModuleData", "races.xml"), "<skins><race id='race_one'><skin gender='0' mesh_maturity_type='adult' skeleton='race_skeleton'/><skin gender='1' mesh_maturity_type='adult' skeleton='race_skeleton'/></race></skins>");
Write(Path.Combine(racePath, "AssetPackages", "fixture.tpac"), "Offline fixture only; not a game resource.");
Write(Path.Combine(mods, "dist", "bad", "SubModule.xml"), "not XML");
Write(Path.Combine(mods, "build", "bad", "SubModule.xml"), "not XML");
var catalog = Discovery.Scan(game, [mods]);
BuilderProject Profile() => new() { ModuleId = "TestReplacement", ModuleName = "Test Replacement", GameRoot = game, ModRoots = [mods], Rules =
    [new TroopRule { RootIds = ["recruit"], RaceModule = "RaceOne", RaceId = "race_one", FaceMode = "fixed", StripArmor = true, IsFemale = true, Age = 25 }] };
bool Error(CheckReport report, string code) => report.Issues.Any(x => x.Severity == "error" && x.Code == code);

Test("nested discovery, registered filename and excluded caches", () =>
{ Assert(catalog.Races.Count == 1 && catalog.Races[0].Id == "race_one", "种族扫描错误"); Assert(catalog.Troops.Count == 5 && catalog.Items.Count == 11, "目录数量错误"); Assert(catalog.Issues.Count == 0, "扫描了缓存或未注册文件"); });
Test("single module directory as custom source", () => Assert(Discovery.Scan(game, [racePath]).Races.Count == 1, "直接模块目录未识别"));
Test("relative project paths resolve beside JSON", () =>
{ var p = Profile(); p.GameRoot = "game"; p.ModRoots = ["mods"]; var file = Path.Combine(fixture, "relative.json"); Json.Save(file, p); var read = Builder.ReadProject(file); Assert(read.GameRoot == game && read.ModRoots[0] == mods, "相对路径依赖当前目录"); });
Test("root selector follows full upgrade tree", () => Assert(Builder.Select(catalog, Profile().Rules[0]).SequenceEqual(new[] { "elite", "recruit", "veteran" }), "分支选择错误"));
Test("unknown troop rejected", () => { var p = Profile(); p.Rules[0].TroopIds.Add("absent"); Assert(Error(Builder.Validate(catalog, p), "troop_missing"), "未知兵种未拒绝"); });
Test("missing race rejected, no human fallback", () => { var p = Profile(); p.Rules[0].RaceId = "absent"; Assert(Error(Builder.Validate(catalog, p), "race_missing"), "无效种族未拒绝"); });
Test("unselected duplicate race provider allowed; actual dependency collisions rejected", () =>
{
    var original = catalog.Modules["RaceOne"];
    var alternative = catalog.Races[0] with { ModuleId = "RaceAlternative" };
    catalog.Races.Add(alternative);
    catalog.Modules["RaceAlternative"] = original with { Id = "RaceAlternative" };
    try
    {
        Assert(Builder.Validate(catalog, Profile()).Status == "pass", "未选择的同种族来源阻止了构建");
        catalog.Modules["RaceOne"] = original with { Dependencies = ["Sandbox", "RaceAlternative"] };
        Assert(Error(Builder.Validate(catalog, Profile()), "race_collision"), "实际依赖种族冲突未拒绝");
    }
    finally { catalog.Modules["RaceOne"] = original; catalog.Modules.Remove("RaceAlternative"); catalog.Races.Remove(alternative); }
});
Test("missing adult gender rejected", () =>
{
    var race = catalog.Races[0]; catalog.Races[0] = race with { Skins = [new(0, "adult", "", "race_skeleton")] };
    try { Assert(Error(Builder.Validate(catalog, Profile()), "skin_missing"), "缺少女性皮肤未拒绝"); } finally { catalog.Races[0] = race; }
});
Test("overlapping rules rejected", () => { var p = Profile(); p.Rules.Add(new() { TroopIds = ["elite"], RaceModule = "RaceOne", RaceId = "race_one" }); Assert(Error(Builder.Validate(catalog, p), "rule_overlap"), "重叠未拒绝"); });
Test("cyclic upgrades rejected", () =>
{ var troop = catalog.Troops["elite"]; catalog.Troops["elite"] = troop with { Upgrades = ["recruit"] }; try { Assert(Error(Builder.Validate(catalog, Profile()), "upgrade_cycle"), "循环未拒绝"); } finally { catalog.Troops["elite"] = troop; } });
Test("module dependency cycle rejected", () =>
{ var module = catalog.Modules["RaceOne"]; catalog.Modules["RaceOne"] = module with { Dependencies = ["RaceOne"] }; try { Assert(Error(Builder.Validate(catalog, Profile()), "dependency"), "依赖循环未拒绝"); } finally { catalog.Modules["RaceOne"] = module; } });
Test("selected duplicate source rejected; unrelated duplicate only warns", () =>
{ catalog.Issues.Add(new("error", "duplicate_module", "duplicate", "RaceOne")); Assert(Error(Builder.Validate(catalog, Profile()), "duplicate_module"), "依赖歧义未拒绝"); catalog.Issues.Clear(); catalog.Issues.Add(new("error", "duplicate_module", "duplicate", "Other")); Assert(Builder.Validate(catalog, Profile()).Status == "pass", "无关合集重复阻止生成"); catalog.Issues.Clear(); });
Test("mercenary tree included; heroes and obsolete excluded", () =>
{
    Assert(Builder.Select(catalog, new() { RootIds = ["mercenary"] }).SequenceEqual(new[] { "mercenary", "mercenary_elite" }), "雇佣兵升级树不完整");
    Assert(!catalog.Troops.ContainsKey("hero_mercenary") && !catalog.Troops.ContainsKey("obsolete_mercenary") && !catalog.Troops.ContainsKey("hidden_mercenary"), "特殊角色被纳入");
    var p = Profile(); p.Rules[0].RootIds = ["mercenary"]; p.Rules[0].Skills = new() { ["Athletics"] = 150 };
    Assert(Builder.Validate(catalog, p).Status == "pass", "雇佣兵无法配置");
    var b = Builder.Build(catalog, p, Path.Combine(output, "mercenary-build"));
    Assert(b.Status == "pass" && b.Targets.Count == 2, "雇佣兵导出失败");
    var replacement = Builder.Replacement(catalog, catalog.Troops["mercenary"], p.Rules[0]);
    Assert((string?)replacement.Attribute("occupation") == "Mercenary" && (string?)replacement.Attribute("id") == "mercenary", "雇佣身份或 ID 被改");
});
Test("skill patch preserves omitted skills, zero and source", () =>
{
    var p = Profile(); var troop = catalog.Troops["recruit"]; var before = troop.Element.ToString();
    Assert(XNode.DeepEquals(troop.Element.Element("skills"), Builder.Replacement(catalog, troop, p.Rules[0]).Element("skills")), "旧工程技能改变");
    p.Rules[0].Skills = new() { ["Athletics"] = 150, ["Riding"] = 0 };
    var skills = Builder.Replacement(catalog, troop, p.Rules[0]).Element("skills")!;
    Assert((int?)skills.Elements("skill").Single(x => (string?)x.Attribute("id") == "Athletics").Attribute("value") == 150, "跑动未覆盖");
    Assert((int?)skills.Elements("skill").Single(x => (string?)x.Attribute("id") == "Riding").Attribute("value") == 0, "零值丢失");
    Assert((int?)skills.Elements("skill").Single(x => (string?)x.Attribute("id") == "Bow").Attribute("value") == 5 && skills.Nodes().OfType<XComment>().Any(), "其他技能或注释丢失");
    Assert(troop.Element.ToString() == before, "原始目录被修改");
    var roundtrip = System.Text.Json.JsonSerializer.Deserialize<BuilderProject>(Json.Write(p), Json.Options)!;
    Assert(roundtrip.Rules[0].Skills!["Riding"] == 0, "工程回读丢失零值");
    var builtSkills = Builder.Build(catalog, p, Path.Combine(output, "skills-build"));
    Assert(builtSkills.Status == "pass" && builtSkills.TransformChecks > 0, "技能转换检查失败");
});
Test("invalid skills rejected", () =>
{
    var p = Profile(); p.Rules[0].Skills = new() { ["athletics"] = 100, ["Bow"] = -1 };
    var report = Builder.Validate(catalog, p); Assert(Error(report, "skill_id") && Error(report, "skill_value"), "无效技能通过");
    try { System.Text.Json.JsonSerializer.Deserialize<TroopRule>("{\"skills\":{\"Bow\":1.5}}", Json.Options); throw new Exception("小数通过"); }
    catch (System.Text.Json.JsonException) { }
});
Test("native duplicate slots use last assignment", () => Assert(Builder.Loadouts(catalog, catalog.Troops["recruit"].Element)[0].Loadout.Slots["Cape"] == "cape2", "重复槽解析不同于游戏"));
Test("strip armor expands civilian templates and keeps weapons", () =>
{ var replacement = Builder.Replacement(catalog, catalog.Troops["recruit"], Profile().Rules[0]); var rosters = Builder.Loadouts(catalog, replacement); Assert(rosters.All(x => !x.Loadout.Slots.Keys.Any(Builder.ArmorSlots.Contains)), "防具未全清除"); Assert(rosters.Any(x => x.Type == "Civilian" && x.Loadout.Slots.GetValueOrDefault("Item0") == "sword1"), "平民武器丢失"); });
Test("explicit loadouts preserve weapon slot candidates", () =>
{
    var p = Profile(); p.Rules[0].BattleLoadouts = [new() { Slots = new() { ["Item0"] = "sword1", ["Item1"] = "twohand1" } }, new() { Slots = new() { ["Item0"] = "sword2", ["Item1"] = "twohand2" } }];
    var rosters = Builder.Loadouts(catalog, Builder.Replacement(catalog, catalog.Troops["recruit"], p.Rules[0])).Where(x => x.Type == "Battle").ToList();
    Assert(rosters.Count == 2 && rosters[1].Loadout.Slots["Item0"] == "sword2" && rosters.All(x => x.Loadout.Slots["Item1"].StartsWith("twohand")), "槽位候选混乱");
});
Test("unknown slots and incompatible items rejected", () =>
{ var p = Profile(); p.Rules[0].BattleLoadouts = [new() { Slots = new() { ["Item0"] = "armor", ["Item7"] = "sword1" } }]; var report = Builder.Validate(catalog, p); Assert(Error(report, "slot") && Error(report, "item_slot"), "装备槽检查失败"); });
Test("unsafe random bow/ammunition combination warns", () =>
{ var p = Profile(); p.Rules[0].BattleLoadouts = [new() { Slots = new() { ["Item0"] = "bow", ["Item1"] = "arrows" } }, new() { Slots = new() { ["Item0"] = "sword1" } }]; Assert(Builder.Validate(catalog, p).Issues.Any(x => x.Code == "random_ammo" && x.Severity == "warning"), "弹药风险无提示"); });
Test("protected module ID and traversal rejected", () =>
{ var p = Profile(); p.ModuleId = "Native"; Assert(Error(Builder.Validate(catalog, p), "module_id"), "原版 ID 未拒绝"); p.ModuleId = "../Escape"; Assert(Error(Builder.Validate(catalog, p), "module_id"), "路径 ID 未拒绝"); Throws(() => Discovery.Inside(mods, "../escape"), "路径越界未拒绝"); });
Test("strict JSON rejects mixed race field", () =>
{ var file = Path.Combine(fixture, "bad.json"); Write(file, "{\"raceIds\":[\"a\",\"b\"]}"); try { Json.Read<TroopRule>(file); throw new Exception("未知字段未拒绝"); } catch (System.Text.Json.JsonException) { } });

Test("original armor averages battle sets, excludes civilian and rounds halves up", () =>
{
    var armor = Builder.OriginalArmor(catalog, catalog.Troops["recruit"]);
    Assert(armor.Mode == "override" && armor.Head == 1 && armor.Body == 12 && armor.Arms == 7 && armor.Legs == 7,
        "多套战斗护甲平均、重复槽或四舍五入错误；平民套不应参与");
    Assert(catalog.Items["sword1"].EquipmentArmor.Body == 0 && catalog.Items["armor"].EquipmentArmor.Head == 0,
        "无护甲物品或省略部位应读取零值");
});
Test("original armor sums all human armor slots and expands battle templates", () =>
{
    var native = catalog.Troops["recruit"];
    var troop = native with { Element = XElement.Parse("""
        <NPCCharacter><Equipments>
          <EquipmentSet id="armor_test"/>
          <equipment slot="Head" id="Item.cape2"/>
          <equipment slot="Gloves" id="Item.cape2"/>
          <equipment slot="Leg" id="Item.cape2"/>
          <equipment slot="HorseHarness" id="Item.armor"/>
          <equipment slot="Item0" id="Item.armor"/>
        </Equipments></NPCCharacter>
        """) };
    catalog.EquipmentSets["armor_test"] = XElement.Parse("""
        <EquipmentRoster><EquipmentSet><equipment slot="Body" id="Item.armor"/><equipment slot="Cape" id="Item.cape2"/></EquipmentSet>
        <EquipmentSet><equipment slot="Body" id="Item.armor"/></EquipmentSet></EquipmentRoster>
        """);
    try
    {
        var armor = Builder.OriginalArmor(catalog, troop);
        Assert(armor.Head == 7 && armor.Body == 31 && armor.Arms == 24 && armor.Legs == 26,
            "模板、公共槽、跨部位贡献或人类槽位范围错误");
    }
    finally { catalog.EquipmentSets.Remove("armor_test"); }
});
Test("original armor includes empty battle sets in average", () =>
{
    var troop = catalog.Troops["recruit"] with { Element = XElement.Parse("""
        <NPCCharacter><Equipments><EquipmentRoster/><EquipmentRoster><equipment slot="Body" id="Item.armor"/></EquipmentRoster></Equipments></NPCCharacter>
        """) };
    var armor = Builder.OriginalArmor(catalog, troop);
    Assert(armor.Head == 0 && armor.Body == 10 && armor.Arms == 5 && armor.Legs == 4, "空装备套未作为零值参与平均");
});
Test("original armor rejects missing equipment data instead of filling false zero", () =>
{
    var native = catalog.Troops["recruit"];
    Throws(() => Builder.OriginalArmor(catalog, native with { Element = XElement.Parse("<NPCCharacter><Equipments><EquipmentRoster civilian='true'/></Equipments></NPCCharacter>") }), "没有战斗装备仍填入零");
    Throws(() => Builder.OriginalArmor(catalog, native with { Element = XElement.Parse("<NPCCharacter><Equipments><EquipmentRoster><equipment slot='Head' id='Item.absent'/></EquipmentRoster></Equipments></NPCCharacter>") }), "缺失防具仍填入零");
    Throws(() => Builder.OriginalArmor(catalog, native with { Element = XElement.Parse("<NPCCharacter/>") }), "缺失装备仍填入零");
});
Test("armor override rejects invalid mode and range", () =>
{
    var p = Profile(); p.Rules[0].Armor = new() { Mode = "unknown", Head = -1, Body = 501 };
    var check = Builder.Validate(catalog, p); Assert(Error(check, "armor_mode") && Error(check, "armor_value"), "护甲检查缺失");
    p.Rules[0].Armor = new() { Mode = "override", Body = 30 }; Assert(Error(Builder.Validate(catalog, p), "armor_incomplete"), "覆盖允许遗漏部位");
    p.Rules[0].Armor = new() { Mode = "inherit", Body = 30 }; Assert(Error(Builder.Validate(catalog, p), "armor_inherit_values"), "继承模式接受了覆盖值");
});
Test("racial default discovery and inheritance", () =>
{
    var file = Path.Combine(racePath, "ModuleData", "rtb_race_armor.xml");
    Write(file, "<RaceArmor schemaVersion='1'><Race id='race_one' head='10' body='30' arms='20' legs='25'/></RaceArmor>");
    try
    {
        var scan = Discovery.Scan(game, [mods]); Assert(scan.Races.Single().DefaultArmor?.Body == 30, "默认值未读取");
        var full = Builder.Build(scan, Profile(), Path.Combine(fixture, "inherit-output"));
        Assert(full.Status == "pass", Json.Write(full));
        Assert(File.Exists(Path.Combine(full.ModulePath!, "bin/Win64_Shipping_Client/RaceTroopBuilder.ArmorRuntime.dll")), "沿用默认值未启用运行组件");
        Assert(XDocument.Load(Path.Combine(full.ModulePath!, "ModuleData/rtb_troop_armor.xml")).Root!.Elements().Count() == 0, "继承复制了依赖默认值");
        Assert(!File.Exists(Path.Combine(full.ModulePath!, "ModuleData/rtb_race_armor.xml")), "输出复制了种族数据");
        Assert(full.DependencyHashes["RaceOne"].ContainsKey("ModuleData/rtb_race_armor.xml"), "默认数据未加入安装校验");
    }
    finally { File.Delete(file); }
});
Test("armor override expands selected tree and ships only own runtime", () =>
{
    var p = Profile(); p.Rules[0].Armor = new() { Mode = "override", Head = 0, Body = 50, Arms = 40, Legs = 45 };
    var full = Builder.Build(catalog, p, Path.Combine(fixture, "armor-output")); Assert(full.Status == "pass", Json.Write(full));
    var entries = XDocument.Load(Path.Combine(full.ModulePath!, "ModuleData/rtb_troop_armor.xml")).Root!.Elements().ToList();
    Assert(entries.Count == 3 && entries.All(x => (string?)x.Attribute("head") == "0" && (string?)x.Attribute("race") == "race_one"), "覆盖数据展开或零值错误");
    Assert(File.Exists(Path.Combine(full.ModulePath!, "bin/Win64_Shipping_Client/0Harmony.dll")), "缺少补丁库");
    Assert(!Directory.EnumerateFiles(full.ModulePath!, "TaleWorlds*.dll", SearchOption.AllDirectories).Any(), "交付了游戏 DLL");
});
Test("official bilingual names, manifest paths and English fallback", () =>
{
    var directory = Path.Combine(corePath, "ModuleData/Languages");
    Write(Path.Combine(directory, "CNs/language_data.xml"), "<LanguageData><LanguageFile xml_path='CNs/strings.xml'/></LanguageData>");
    Write(Path.Combine(directory, "CNs/strings.xml"), "<base><strings><string id='name_recruit' text='测试新兵'/><string id='item' text='测试武器'/></strings></base>");
    var scan = Discovery.Scan(game, [mods]);
    Assert(scan.Troops["recruit"].NameZh == "测试新兵" && scan.Troops["recruit"].NameEn == "recruit", "双语错误");
    Assert(scan.Troops["veteran"].DisplayName("zh-CN") == "veteran", "缺失中文未回退");
    Assert(scan.Items["sword1"].SearchText.Contains("测试武器") && scan.Items["sword1"].SearchText.Contains("sword1"), "搜索遗漏语言");
    scan.Items["sword1"].Language = "en"; Assert(scan.Items["sword1"].DisplayName == "sword1", "英文切换错误");
});

CheckReport? built = null;
var buildRoot = Path.Combine(fixture, "output"); var reportFile = Path.Combine(buildRoot, "TestReplacement.validation.json");
Test("XSLT transformation, localization and untouched heroes", () =>
{
    built = Builder.Build(catalog, Profile(), buildRoot); Assert(built.Status == "pass" && built.TransformChecks == 9, Json.Write(built));
    var xslt = new XslCompiledTransform(); xslt.Load(Path.Combine(built.ModulePath!, "ModuleData", "rtb_troops.xslt"));
    using var writer = new StringWriter(); xslt.Transform(Path.Combine(corePath, "ModuleData", "troops.xml"), null, writer);
    var result = XDocument.Parse(writer.ToString()); var recruit = result.Root!.Elements().Single(x => (string?)x.Attribute("id") == "recruit");
    Assert((string?)recruit.Attribute("name") == "{=name_recruit}recruit", "本地化花括号被 XSLT 执行");
    Assert((string?)recruit.Attribute("race") == "race_one", "目标未替换");
    Assert(result.Root.Elements().Single(x => (string?)x.Attribute("id") == "hero").Attribute("race") == null, "修改了英雄");
    Assert(!Directory.EnumerateFiles(built.ModulePath!, "*.tpac", SearchOption.AllDirectories).Any() && !File.Exists(Path.Combine(built.ModulePath!, "ModuleData", "skins.xml")), "包含种族资源");
    Assert(built.LoadOrder.IndexOf("RaceOne") < built.LoadOrder.IndexOf("TestReplacement"), "依赖加载顺序错误");
});
Test("package contains only generated module and report", () =>
{
    var archivePath = Builder.Package(reportFile, Path.Combine(fixture, "delivery.zip")); using var zip = ZipFile.OpenRead(archivePath);
    Assert(zip.Entries.Any(x => x.FullName == "TestReplacement/SubModule.xml") && zip.Entries.All(x => !x.FullName.Contains("RaceOne/")), "交付包混入依赖");
});
Test("build never silently overwrites old output", () => Throws(() => Builder.Build(catalog, Profile(), buildRoot), "旧构建被覆盖"));
Test("install missing dependency changes nothing", () =>
{ Throws(() => Builder.Install(reportFile, game), "缺依赖仍安装"); Assert(!Directory.Exists(Path.Combine(game, "Modules", "TestReplacement")), "缺依赖产生目标模块"); });
var installedRace = Path.Combine(game, "Modules", "RaceOne");
foreach (var file in Directory.EnumerateFiles(racePath, "*", SearchOption.AllDirectories))
{ var destination = Path.Combine(installedRace, Path.GetRelativePath(racePath, file)); Directory.CreateDirectory(Path.GetDirectoryName(destination)!); File.Copy(file, destination); }
Test("install matching dependencies and back up previous module", () =>
{
    Builder.Install(reportFile, game); var target = Path.Combine(game, "Modules", "TestReplacement");
    Assert(Builder.HashFiles(target).OrderBy(x => x.Key).SequenceEqual(built!.FileHashes.OrderBy(x => x.Key)), "安装哈希不符");
    Write(Path.Combine(target, "old-user-note.txt"), "preserve in backup"); var backups = Path.Combine(fixture, "backups"); Builder.Install(reportFile, game, backups);
    using var zip = ZipFile.OpenRead(Directory.GetFiles(backups, "*.zip").Single()); Assert(zip.Entries.Any(x => x.FullName == "old-user-note.txt"), "旧版内容未备份");
});
Test("installed dependency mismatch rejected", () =>
{ var file = Path.Combine(installedRace, "AssetPackages", "fixture.tpac"); var original = File.ReadAllText(file); File.WriteAllText(file, "mismatch"); try { Throws(() => Builder.Install(reportFile, game), "不匹配依赖仍安装"); } finally { File.WriteAllText(file, original); } });
Test("locked existing module rolls back without data loss", () =>
{
    var target = Path.Combine(game, "Modules", "TestReplacement"); var file = Path.Combine(target, "SubModule.xml"); var before = Builder.HashFiles(target);
    using (var locked = File.Open(file, FileMode.Open, FileAccess.Read, FileShare.Read)) Throws(() => Builder.Install(reportFile, game), "占用模块仍被覆盖");
    Assert(before.OrderBy(x => x.Key).SequenceEqual(Builder.HashFiles(target).OrderBy(x => x.Key)), "失败后旧模块丢失");
    Assert(!Directory.EnumerateDirectories(Path.Combine(game, "Modules"), "TestReplacement.rtb-stage-*").Any(), "失败后留下重复 ID 暂存模块");
});
Test("modified output fails packaging and installation", () =>
{ var file = Path.Combine(built!.ModulePath!, "ModuleData", "rtb_troops.xml"); File.AppendAllText(file, "<!--changed-->"); Throws(() => Builder.Package(reportFile, Path.Combine(fixture, "bad-package.zip")), "修改产物仍可打包"); Throws(() => Builder.Install(reportFile, game), "修改产物仍可安装"); });

if (args.Length > 1 && args[1] == "--local-game")
{
    Test("local v1.4.8 every soldier equipment resolves", () =>
    {
        var real = Discovery.Scan(); var profile = new BuilderProject { ModuleId = "OfflineAllTroops", ModuleName = "Offline All Troops", Rules =
            [new() { TroopIds = real.Troops.Keys.ToList(), RaceModule = "YueQingShuRace", RaceId = "yqs_default", FaceMode = "fixed", StripArmor = true, IsFemale = true, Age = 25 }] };
        var mercenaries = real.Troops.Values.Where(x => (string?)x.Element.Attribute("occupation") == "Mercenary").ToList();
        foreach (var troop in real.Troops.Values)
        {
            var armor = Builder.OriginalArmor(real, troop);
            Assert(new[] { armor.Head, armor.Body, armor.Arms, armor.Legs }.All(x => x >= 0 && x <= 500),
                "本机原兵种护甲不可填入：" + troop.Id);
        }
        Assert(mercenaries.Count == 14, "本机雇佣兵数量异常");
        var official = Localization.ReadChinese(real.Modules.Values.Where(x => Discovery.OfficialIds.Contains(x.Id)));
        foreach (var mercenary in mercenaries)
            Assert(official.TryGetValue(mercenary.NameKey, out var chineseName) && mercenary.NameZh == chineseName && chineseName.Length > 0, "雇佣兵未使用官方中文：" + mercenary.Id);
        Assert(Builder.Select(real, new() { RootIds = ["sword_sisters_sister_t3", "eastern_mercenary", "western_mercenary"] }).Count == 14, "本机雇佣兵分支不全");
        var report = Builder.Validate(real, profile); Assert(report.Status == "pass", Json.Write(report));
        var full = Builder.Build(real, profile, Path.Combine(output, "all-troops-" + Guid.NewGuid().ToString("N")));
        Assert(full.TransformChecks > 1000 && full.Targets.Count == real.Troops.Count, "本机全量转换检查不完整");
    });
}
var summary = new { status = failures == 0 ? "pass" : "fail", count = results.Count, failures, fixture, tests = results };
Json.Save(Path.Combine(output, "tests.json"), summary); Console.WriteLine(Json.Write(summary)); return failures == 0 ? 0 : 1;
