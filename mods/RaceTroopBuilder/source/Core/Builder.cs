using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using System.Xml;
using System.Xml.Linq;
using System.Xml.Xsl;

namespace RaceTroopBuilder.Core;

public static partial class Builder
{
    public static readonly string[] Slots = ["Item0", "Item1", "Item2", "Item3", "Head", "Cape", "Body", "Leg", "Gloves", "Horse", "HorseHarness"];
    public static readonly string[] SkillIds = ["OneHanded", "TwoHanded", "Polearm", "Bow", "Crossbow", "Throwing", "Athletics", "Riding"];
    public static readonly string[] ArmorSlots = ["Head", "Cape", "Body", "Leg", "Gloves"];
    [GeneratedRegex("^[A-Za-z][A-Za-z0-9_-]{0,63}$")] private static partial Regex IdPattern();
    [GeneratedRegex("^v[0-9]+\\.[0-9]+\\.[0-9]+$")] private static partial Regex VersionPattern();
    private static readonly XNamespace Xsl = "http://www.w3.org/1999/XSL/Transform";

    public static BuilderProject ReadProject(string file)
    {
        var project = Json.Read<BuilderProject>(file);
        var directory = Path.GetDirectoryName(Path.GetFullPath(file))!;
        if (!string.IsNullOrWhiteSpace(project.GameRoot)) project.GameRoot = Path.GetFullPath(project.GameRoot, directory);
        project.ModRoots = project.ModRoots.Select(x => Path.GetFullPath(x, directory)).ToList();
        return project;
    }

    public static List<string> Select(Catalog catalog, TroopRule rule)
    {
        var ids = new HashSet<string>(rule.TroopIds, StringComparer.Ordinal);
        var pending = new Stack<string>(rule.RootIds);
        if (!string.IsNullOrWhiteSpace(rule.Culture))
            foreach (var troop in catalog.Troops.Values.Where(x => x.Culture == Discovery.Ref(rule.Culture))) ids.Add(troop.Id);
        var visited = new HashSet<string>(StringComparer.Ordinal);
        while (pending.TryPop(out var id))
        {
            if (!visited.Add(id)) continue;
            ids.Add(id);
            if (catalog.Troops.TryGetValue(id, out var troop)) foreach (var next in troop.Upgrades) pending.Push(next);
        }
        return ids.Order(StringComparer.Ordinal).ToList();
    }

    public static List<string> DependencyOrder(Catalog catalog, IEnumerable<string> ids)
    {
        var ordered = new List<string>();
        var states = new Dictionary<string, int>(StringComparer.Ordinal);
        void Visit(string id)
        {
            if (states.TryGetValue(id, out var state))
            { if (state == 1) throw new InvalidDataException("模块依赖循环：" + id); return; }
            if (!catalog.Modules.TryGetValue(id, out var module)) throw new InvalidDataException("缺少必需依赖：" + id);
            states[id] = 1;
            foreach (var dependency in module.Dependencies) Visit(dependency);
            states[id] = 2; ordered.Add(id);
        }
        foreach (var id in ids.Distinct(StringComparer.Ordinal)) Visit(id);
        return ordered;
    }

    public static CheckReport Validate(Catalog catalog, BuilderProject project)
    {
        var report = new CheckReport { GameVersion = catalog.GameVersion };
        void Error(string code, string message, string? subject = null) => report.Issues.Add(new("error", code, message, subject));
        if (project.DisplayLanguage is not ("zh-CN" or "en")) Error("language", "displayLanguage 只能为 zh-CN 或 en。");
        if (project.SchemaVersion != 1) Error("schema_version", "仅支持 schemaVersion=1。");
        if (!IdPattern().IsMatch(project.ModuleId) || IsReserved(project.ModuleId)) Error("module_id", "模块 ID 无效或属于原版保留名称。");
        if (!VersionPattern().IsMatch(project.Version)) Error("version", "版本应为 v主.次.修订。");
        if (string.IsNullOrWhiteSpace(project.ModuleName) || project.ModuleName.Any(x => x > 127 || char.IsControl(x)))
            Error("module_name", "启动器模块名称必须是非空英文名称。");
        if (catalog.GameVersion != "v1.4.8") Error("game_version", "当前生成器仅验证了 v1.4.8；其他版本须先更新适配和检查。");
        if (project.Rules.Count == 0) Error("empty_project", "至少配置一个兵种替换规则。");
        var owners = new Dictionary<string, int>(StringComparer.Ordinal);
        var dependencies = new List<string> { "Native", "SandBoxCore", "Sandbox" };
        if (catalog.Modules.ContainsKey("StoryMode")) dependencies.Add("StoryMode");
        for (var ruleIndex = 0; ruleIndex < project.Rules.Count; ruleIndex++)
        {
            var rule = project.Rules[ruleIndex];
            var subject = "rules[" + ruleIndex + "]";
            var raceMatches = catalog.Races.Where(x => x.ModuleId == rule.RaceModule && x.Id == rule.RaceId).ToList();
            var race = raceMatches.Count == 1 ? raceMatches[0] : null;
            if (race == null) Error("race_missing", "未找到指定模块的已注册种族：" + rule.RaceModule + "/" + rule.RaceId, subject);
            else
            {
                dependencies.Add(race.ModuleId);
                if (catalog.Races.Where(x => x.Id == race.Id).Select(x => x.ModuleId).Distinct().Count() > 1)
                    Error("race_collision", "不同模块使用相同种族 ID，不能确定实际解析结果。", race.Id);
            }
            if (rule.FaceMode is not ("preserve" or "fixed")) Error("face_mode", "faceMode 只能是 preserve 或 fixed。", subject);
            if (rule.Age is < 18 or > 100) Error("age", "普通士兵年龄须在 18～100 岁之间。", subject);
            if (rule.Skills != null)
                foreach (var (skill, value) in rule.Skills)
                {
                    if (!SkillIds.Contains(skill)) Error("skill_id", "不支持的技能 ID：" + skill, subject);
                    if (value < 0) Error("skill_value", "技能值必须为非负整数。", subject);
                }
            if (rule.Armor != null)
            {
                var armor = rule.Armor;
                if (armor.Mode == "override" && !(armor.HeadSet && armor.BodySet && armor.ArmsSet && armor.LegsSet))
                    Error("armor_incomplete", "覆盖模式须明确提供 head/body/arms/legs，包括零值。", subject);
                if (armor.Mode is not ("inherit" or "override")) Error("armor_mode", "护甲模式只能为 inherit 或 override。", subject);
                if (new[] { armor.Head, armor.Body, armor.Arms, armor.Legs }.Any(x => x < 0 || x > 500))
                    Error("armor_value", "四部位护甲须为 0～500 的整数。", subject);
                if (armor.Mode == "inherit" && new[] { armor.Head, armor.Body, armor.Arms, armor.Legs }.Any(x => x != 0))
                    Error("armor_inherit_values", "沿用模式不接受覆盖值；请改为 override。", subject);
            }
            if (race != null && rule.Armor?.Mode != "override" && race.DefaultArmor == null)
                report.Issues.Add(new("warning", "race_armor_undeclared", "种族未声明固有护甲协议；不干预现有机制，不能确认其固定值。", subject));
            var targets = Select(catalog, rule);
            if (targets.Count == 0) Error("empty_selection", "规则没有选中任何兵种。", subject);
            foreach (var id in targets)
            {
                if (!owners.TryAdd(id, ruleIndex)) { Error("rule_overlap", "同一兵种被多条规则选择，请先解除重叠。", id); continue; }
                if (!catalog.Troops.TryGetValue(id, out var troop)) { Error("troop_missing", "原版兵种不存在或不是可编辑的普通士兵。", id); continue; }
                if (race != null && !race.Skins.Any(x => x.Gender == ((rule.IsFemale ?? troop.IsFemale) ? 1 : 0) && x.Maturity == "adult"))
                    Error("skin_missing", "种族没有所选性别的成年 skin。", id);
                if (race != null && rule.FaceMode == "preserve")
                    report.Issues.Add(new("warning", "face_preserved", "保留原版脸参数；完整固定身体通常应选择 fixed。", id));
                foreach (var upgrade in troop.Upgrades)
                    if (!catalog.Troops.ContainsKey(upgrade)) Error("upgrade_missing", "升级目标不存在：" + upgrade, id);
                try
                {
                    var element = Replacement(catalog, troop, rule);
                    ValidateEquipment(catalog, element, report, id);
                }
                catch (InvalidDataException e) { Error("equipment_resolution", e.Message, id); }
            }
        }
        report.Targets = owners.Keys.Order(StringComparer.Ordinal).ToList();
        try
        {
            report.LoadOrder = DependencyOrder(catalog, dependencies);
            if (report.LoadOrder.Contains(project.ModuleId)) Error("dependency_self", "输出模块 ID 与依赖模块相同。");
            foreach (var issue in catalog.Issues)
            {
                // Unrelated collection modules often repeat IDs in editable set directories.
                var related = issue.Subject != null && report.LoadOrder.Contains(issue.Subject);
                report.Issues.Add(issue.Code == "duplicate_module" && !related ? issue with { Severity = "warning" } : issue);
            }
            foreach (var id in report.LoadOrder)
            {
                report.DependencyVersions[id] = catalog.Modules[id].Version;
                if (!Discovery.OfficialIds.Contains(id)) CheckDependencyFiles(catalog.Modules[id], report);
            }
            report.LoadOrder.Add(project.ModuleId);
        }
        catch (InvalidDataException e) { Error("dependency", e.Message); }
        var states = new Dictionary<string, int>(StringComparer.Ordinal);
        void Walk(string id)
        {
            if (states.TryGetValue(id, out var state)) { if (state == 1) Error("upgrade_cycle", "升级树存在循环。", id); return; }
            states[id] = 1;
            if (catalog.Troops.TryGetValue(id, out var troop))
            {
                if (troop.Upgrades.Count != troop.Upgrades.Distinct().Count()) Error("upgrade_duplicate", "升级目标重复。", id);
                foreach (var next in troop.Upgrades) Walk(next);
            }
            states[id] = 2;
        }
        foreach (var id in report.Targets) Walk(id);
        return report;
    }

    private static bool IsReserved(string id) => Discovery.OfficialIds.Contains(id, StringComparer.OrdinalIgnoreCase)
        || new[] { "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9" }.Contains(id, StringComparer.OrdinalIgnoreCase);

    private static void CheckDependencyFiles(ModuleInfo module, CheckReport report)
    {
        try
        {
            var project = Path.Combine(module.Path, "ModuleData", "project.mbproj");
            if (File.Exists(project)) foreach (var entry in Discovery.Xml(project).Root?.Elements("file") ?? [])
                _ = Discovery.Xml(Discovery.Inside(module.Path, (string?)entry.Attribute("name") ?? ""));
            foreach (var child in module.Descriptor.Element("SubModules")?.Elements("SubModule") ?? [])
            {
                var dll = (string?)child.Element("DLLName")?.Attribute("value");
                if (!string.IsNullOrWhiteSpace(dll) && !File.Exists(Discovery.Inside(module.Path, "bin/Win64_Shipping_Client/" + dll)))
                    report.Issues.Add(new("error", "dependency_dll_missing", "依赖模块缺少运行 DLL：" + dll, module.Id));
            }
            if (!Directory.Exists(Path.Combine(module.Path, "AssetPackages")) || !Directory.EnumerateFiles(Path.Combine(module.Path, "AssetPackages"), "*.tpac").Any())
                report.Issues.Add(new("warning", "dependency_assets", "模块未包含 TPAC；其资源可能由其他依赖提供，请核对。", module.Id));
        }
        catch (Exception e) when (e is IOException or XmlException or InvalidDataException)
        { report.Issues.Add(new("error", "dependency_files", e.Message, module.Id)); }
    }

    public static List<(string Type, Loadout Loadout)> Loadouts(Catalog catalog, XElement troop)
    {
        var result = new List<(string, Loadout)>();
        var equipments = troop.Elements().FirstOrDefault(x => x.Name.LocalName.Equals("Equipments", StringComparison.OrdinalIgnoreCase));
        if (equipments == null) throw new InvalidDataException("兵种没有 Equipments；尚不支持通过 battleTemplate/civilianTemplate 隐式继承的装备。" );
        foreach (var entry in equipments.Elements())
        {
            var type = EquipmentType(entry);
            if (entry.Name.LocalName.Equals("EquipmentRoster", StringComparison.OrdinalIgnoreCase)) result.Add((type, ParseLoadout(entry)));
            else if (entry.Name.LocalName.Equals("EquipmentSet", StringComparison.OrdinalIgnoreCase))
            {
                var id = Discovery.Ref((string?)entry.Attribute("id") ?? "");
                if (!catalog.EquipmentSets.TryGetValue(id, out var set)) throw new InvalidDataException("找不到原版装备集合：" + id);
                var sets = set.Elements().Where(x => x.Name.LocalName == "EquipmentSet" && EquipmentType(x) == type).ToList();
                if (sets.Count == 0) throw new InvalidDataException("装备集合不含所需类型：" + id + "/" + type);
                foreach (var child in sets) result.Add((type, ParseLoadout(child)));
            }
        }
        var common = ParseLoadout(equipments);
        foreach (var (_, loadout) in result) foreach (var (slot, item) in common.Slots) loadout.Slots[slot] = item;
        return result;
    }

    public static ArmorSettings OriginalArmor(Catalog catalog, TroopInfo troop)
    {
        var loadouts = Loadouts(catalog, troop.Element).Where(x => x.Type == "Battle").ToList();
        if (loadouts.Count == 0) throw new InvalidDataException("兵种没有可读取的原版战斗装备套。" );
        var totals = new List<RaceTroopBuilder.Armor.ArmorValues>();
        foreach (var (_, loadout) in loadouts)
        {
            var total = new RaceTroopBuilder.Armor.ArmorValues();
            foreach (var slot in ArmorSlots)
            {
                if (!loadout.Slots.TryGetValue(slot, out var id) || string.IsNullOrWhiteSpace(id)) continue;
                if (!catalog.Items.TryGetValue(id, out var item))
                    throw new InvalidDataException("找不到原版防具物品：" + id);
                total.Head += item.EquipmentArmor.Head; total.Body += item.EquipmentArmor.Body;
                total.Arms += item.EquipmentArmor.Arms; total.Legs += item.EquipmentArmor.Legs;
            }
            totals.Add(total);
        }
        // Equal-weight native battle sets; round only after averaging the complete sums.
        int Average(Func<RaceTroopBuilder.Armor.ArmorValues, int> value) =>
            checked((int)Math.Round(totals.Average(value), MidpointRounding.AwayFromZero));
        return new() { Mode = "override", Head = Average(x => x.Head), Body = Average(x => x.Body),
            Arms = Average(x => x.Arms), Legs = Average(x => x.Legs) };
    }

    private static string EquipmentType(XElement node) =>
        string.Equals((string?)node.Attribute("equipmentType"), "Civilian", StringComparison.OrdinalIgnoreCase) || (bool?)node.Attribute("civilian") == true ? "Civilian" : "Battle";
    private static Loadout ParseLoadout(XElement entry)
    {
        var result = new Loadout();
        foreach (var equipment in entry.Elements().Where(x => x.Name.LocalName.Equals("equipment", StringComparison.OrdinalIgnoreCase)))
        {
            var slot = (string?)equipment.Attribute("slot") ?? throw new InvalidDataException("装备缺少 slot。");
            // Native XML itself repeats some Cape slots. Equipment.DeserializeNode assigns in order;
            // keep the final value, matching the game rather than rejecting valid native definitions.
            result.Slots[slot] = Discovery.Ref((string?)equipment.Attribute("id") ?? "");
        }
        return result;
    }

    public static XElement Replacement(Catalog catalog, TroopInfo troop, TroopRule rule)
    {
        var element = new XElement(troop.Element);
        element.SetAttributeValue("race", rule.RaceId);
        if (rule.Skills is { Count: > 0 })
        {
            var skills = element.Element("skills");
            if (skills == null) { skills = new XElement("skills"); element.Add(skills); }
            foreach (var (id, value) in rule.Skills)
            {
                var matches = skills.Elements("skill").Where(x => (string?)x.Attribute("id") == id).ToList();
                var skill = matches.FirstOrDefault();
                if (skill == null) { skill = new XElement("skill", new XAttribute("id", id)); skills.Add(skill); }
                skill.SetAttributeValue("value", value);
                foreach (var duplicate in matches.Skip(1)) duplicate.Remove();
            }
        }
        if (rule.IsFemale != null) element.SetAttributeValue("is_female", rule.IsFemale.Value ? "true" : "false");
        if (rule.Age != null) element.SetAttributeValue("age", rule.Age.Value);
        if (!string.IsNullOrWhiteSpace(rule.Name)) element.SetAttributeValue("name", rule.Name);
        if (rule.FaceMode == "fixed")
        {
            var properties = new XElement("BodyProperties", new XAttribute("version", "4"), new XAttribute("age", rule.Age ?? 25),
                new XAttribute("weight", "0.5"), new XAttribute("build", "0.5"), new XAttribute("key", new string('0', 128)));
            var face = new XElement("face", properties, new XElement("BodyPropertiesMax", properties.Attributes()));
            element.Element("face")?.Remove(); element.AddFirst(face);
            element.SetAttributeValue("face_mesh_cache", "false");
        }
        else if (rule.Age != null)
            foreach (var body in element.Element("face")?.Elements().Where(x => x.Name.LocalName is "BodyProperties" or "BodyPropertiesMax") ?? [])
                body.SetAttributeValue("age", rule.Age.Value);
        if (rule.StripArmor || rule.BattleLoadouts != null || rule.CivilianLoadouts != null)
        {
            var originals = Loadouts(catalog, element);
            var battle = rule.BattleLoadouts ?? originals.Where(x => x.Type == "Battle").Select(x => x.Loadout).ToList();
            var civilian = rule.CivilianLoadouts ?? originals.Where(x => x.Type == "Civilian").Select(x => x.Loadout).ToList();
            var equipments = new XElement("Equipments");
            foreach (var (type, list) in new[] { ("Battle", battle), ("Civilian", civilian) })
                foreach (var loadout in list)
                {
                    var roster = new XElement("EquipmentRoster", new XAttribute("equipmentType", type));
                    foreach (var slot in Slots)
                        if (loadout.Slots.TryGetValue(slot, out var id) && !string.IsNullOrWhiteSpace(id) && (!rule.StripArmor || !ArmorSlots.Contains(slot)))
                            roster.Add(new XElement("equipment", new XAttribute("slot", slot), new XAttribute("id", "Item." + Discovery.Ref(id))));
                    // Preserve unknown slots until validation rejects them, instead of silently dropping input.
                    foreach (var (slot, id) in loadout.Slots.Where(x => !Slots.Contains(x.Key)))
                        roster.Add(new XElement("equipment", new XAttribute("slot", slot), new XAttribute("id", "Item." + Discovery.Ref(id))));
                    equipments.Add(roster);
                }
            element.Elements().Where(x => x.Name.LocalName.Equals("Equipments", StringComparison.OrdinalIgnoreCase)).Remove();
            element.Add(equipments);
        }
        return element;
    }

    private static void ValidateEquipment(Catalog catalog, XElement element, CheckReport report, string id)
    {
        var all = Loadouts(catalog, element);
        if (!all.Any(x => x.Type == "Battle")) report.Issues.Add(new("error", "battle_loadout_empty", "兵种至少需要一套战斗装备配置。", id));
        foreach (var (_, loadout) in all)
        foreach (var (slot, itemId) in loadout.Slots)
        {
            if (!Slots.Contains(slot)) { report.Issues.Add(new("error", "slot", "未知装备槽：" + slot, id)); continue; }
            if (!catalog.Items.TryGetValue(Discovery.Ref(itemId), out var item)) { report.Issues.Add(new("error", "item_missing", "原版物品不存在：" + itemId, id)); continue; }
            var fits = slot switch
            {
                "Head" => item.Type == "HeadArmor", "Cape" => item.Type == "Cape", "Body" => item.Type == "BodyArmor",
                "Leg" => item.Type == "LegArmor", "Gloves" => item.Type == "HandArmor", "Horse" => item.Type == "Horse",
                "HorseHarness" => item.Type == "HorseHarness", _ => IsWeapon(item.Type)
            };
            if (!fits) report.Issues.Add(new("error", "item_slot", $"{itemId} ({item.Type}) 不适合 {slot} 槽。", id));
        }
        foreach (var type in new[] { "Battle", "Civilian" })
        {
            var loadouts = all.Where(x => x.Type == type).Select(x => x.Loadout).ToList();
            var equipped = loadouts.SelectMany(x => x.Slots.Values).Select(x => catalog.Items.GetValueOrDefault(Discovery.Ref(x))).ToList();
            var itemTypes = equipped.Select(x => x?.WeaponClass == "Sling" ? "Sling" : x?.Type).ToList();
            foreach (var (weapon, ammo) in new[] { ("Bow", "Arrows"), ("Crossbow", "Bolts"), ("Sling", "SlingStones") })
            {
                if (!itemTypes.Contains(weapon)) continue;
                var reliableAmmo = Enumerable.Range(0, 4).Any(i => loadouts.All(l => l.Slots.TryGetValue("Item" + i, out var item)
                    && catalog.Items.GetValueOrDefault(Discovery.Ref(item))?.Type == ammo));
                if (!reliableAmmo) report.Issues.Add(new("warning", "random_ammo", $"{type} 配置含 {weapon}，但槽位随机可能缺少 {ammo}；建议固定一个弹药槽。", id));
            }
            if (loadouts.Any(x => x.Slots.ContainsKey("HorseHarness")) && loadouts.Any(x => !x.Slots.ContainsKey("Horse")))
                report.Issues.Add(new("warning", "random_harness", $"{type} 随机装备可能有马具但没有坐骑。", id));
        }
    }

    public static bool IsWeapon(string type) => type is "OneHandedWeapon" or "TwoHandedWeapon" or "Polearm" or "Bow" or "Crossbow" or "Arrows" or "Bolts" or "Thrown" or "Shield"
        or "Sling" or "SlingStones" or "Pistol" or "Musket" or "Bullets" or "Banner";

    public static object Preview(Catalog catalog, BuilderProject project)
    {
        var report = Validate(catalog, project);
        if (report.Status != "pass") return new { report, changes = Array.Empty<object>() };
        var changes = project.Rules.SelectMany(rule => Select(catalog, rule).Select(id => new
        {
            id, beforeXml = catalog.Troops[id].Element.ToString(), afterXml = Replacement(catalog, catalog.Troops[id], rule).ToString(), armor = new { mode = rule.Armor?.Mode ?? "inherit", raceDefault = catalog.Races.First(x => x.Id == rule.RaceId && x.ModuleId == rule.RaceModule).DefaultArmor, troopOverride = rule.Armor?.Mode == "override" ? rule.Armor : null }
        })).ToList();
        return new { report, changes };
    }

    public static CheckReport Build(Catalog catalog, BuilderProject project, string outputRoot)
    {
        var report = Validate(catalog, project);
        if (report.Status != "pass") return report;
        var root = Path.GetFullPath(outputRoot);
        var modulePath = Discovery.Inside(root, project.ModuleId);
        if (Directory.Exists(modulePath)) throw new IOException("输出目录已存在；请选择新的构建目录，保留旧构建：" + modulePath);
        if (Path.GetFullPath(root).StartsWith(Path.Combine(catalog.GameRoot, "Modules") + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)
            || root.Equals(Path.Combine(catalog.GameRoot, "Modules"), StringComparison.OrdinalIgnoreCase))
            throw new IOException("请先构建到工程输出目录，再使用 install 安装。");
        // Verify everything in memory before creating the deliverable.
        var replacements = project.Rules.SelectMany(rule => Select(catalog, rule).Select(id => Replacement(catalog, catalog.Troops[id], rule)))
            .ToDictionary(x => (string)x.Attribute("id")!, StringComparer.Ordinal);
        var stylesheet = new XDocument(new XElement(Xsl + "stylesheet", new XAttribute("version", "1.0"), new XAttribute(XNamespace.Xmlns + "xsl", Xsl),
            new XElement(Xsl + "output", new XAttribute("method", "xml"), new XAttribute("encoding", "utf-8"), new XAttribute("indent", "yes")),
            new XElement(Xsl + "template", new XAttribute("match", "@*|node()"), new XElement(Xsl + "copy", new XElement(Xsl + "apply-templates", new XAttribute("select", "@*|node()"))))));
        foreach (var (id, replacement) in replacements)
        {
            if (!IdPattern().IsMatch(id)) throw new InvalidDataException("兵种 ID 不适合精确 XSLT 匹配：" + id);
            stylesheet.Root!.Add(new XElement(Xsl + "template", new XAttribute("match", $"NPCCharacter[@id='{id}']"), EscapeLiteral(replacement)));
        }
        var transform = new XslCompiledTransform();
        using (var reader = stylesheet.CreateReader()) transform.Load(reader, new XsltSettings(false, false), null);
        var documents = catalog.TroopDocuments.ToList();
        foreach (var dependency in report.LoadOrder.Where(x => x != project.ModuleId && !Discovery.OfficialIds.Contains(x)))
            foreach (var file in Discovery.RegisteredFiles(catalog.Modules[dependency], "NPCCharacters")) documents.Add((file, Discovery.Xml(file)));
        foreach (var (path, document) in documents)
        {
            var transformed = Apply(transform, document);
            var originals = document.Root?.Elements("NPCCharacter").ToList() ?? [];
            var actual = transformed.Root?.Elements("NPCCharacter").ToList() ?? [];
            if (originals.Count != actual.Count) throw new InvalidDataException("转换改变了兵种数量：" + path);
            for (var i = 0; i < originals.Count; i++)
            {
                var id = (string?)originals[i].Attribute("id") ?? "";
                var expected = replacements.GetValueOrDefault(id) ?? originals[i];
                if (!XNode.DeepEquals(Normalize(expected), Normalize(actual[i]))) throw new InvalidDataException("转换结果与目标不符：" + path + " / " + id);
                report.TransformChecks++;
            }
        }
        var useArmor = project.Rules.Any(x => x.Armor?.Mode == "override") || report.LoadOrder.Where(x => x != project.ModuleId)
            .Any(x => File.Exists(Path.Combine(catalog.Modules[x].Path, "ModuleData", RaceTroopBuilder.Armor.ArmorProtocol.RaceFile)));
        var runtimeEntry = new XElement("SubModule", new XElement("Name", new XAttribute("value", "Race Troop Armor")),
            new XElement("DLLName", new XAttribute("value", "RaceTroopBuilder.ArmorRuntime.dll")),
            new XElement("SubModuleClassType", new XAttribute("value", "RaceTroopBuilder.ArmorRuntime.SubModule")),
            new XElement("Tags", new XElement("Tag", new XAttribute("key", "DedicatedServerType"), new XAttribute("value", "none")),
                new XElement("Tag", new XAttribute("key", "IsNoRenderModeElement"), new XAttribute("value", "false"))));
        var module = new XDocument(new XElement("Module",
            new XElement("Name", new XAttribute("value", project.ModuleName)), new XElement("Id", new XAttribute("value", project.ModuleId)),
            new XElement("Version", new XAttribute("value", project.Version)), new XElement("DefaultModule", new XAttribute("value", "false")),
            new XElement("ModuleCategory", new XAttribute("value", "Singleplayer")), new XElement("ModuleType", new XAttribute("value", "Community")),
            new XElement("SingleplayerModule", new XAttribute("value", "true")), new XElement("MultiplayerModule", new XAttribute("value", "false")),
            new XElement("DependedModules", report.LoadOrder.Where(x => x != project.ModuleId).Select(x => new XElement("DependedModule", new XAttribute("Id", x)))),
            new XElement("SubModules", useArmor ? runtimeEntry : null), new XElement("Xmls", new XElement("XmlNode", new XElement("XmlName", new XAttribute("id", "NPCCharacters"), new XAttribute("path", "rtb_troops")),
                new XElement("IncludedGameTypes", new XElement("GameType", new XAttribute("value", "Campaign")), new XElement("GameType", new XAttribute("value", "CampaignStoryMode")))))));
        Directory.CreateDirectory(Path.Combine(modulePath, "ModuleData"));
        if (useArmor)
        {
            var bin = Path.Combine(modulePath, "bin", "Win64_Shipping_Client"); Directory.CreateDirectory(bin);
            foreach (var name in new[] { "ArmorRuntime.dll", "0Harmony.dll", "Harmony-LICENSE.txt" })
            {
                using var input = typeof(Builder).Assembly.GetManifestResourceStream(name) ?? throw new InvalidDataException("缺少护甲运行组件：" + name);
                using var output = File.Create(Path.Combine(bin, name == "ArmorRuntime.dll" ? "RaceTroopBuilder.ArmorRuntime.dll" : name)); input.CopyTo(output);
            }
            var armorXml = new XElement("TroopArmor", new XAttribute("schemaVersion", "1"));
            foreach (var rule in project.Rules.Where(x => x.Armor?.Mode == "override"))
            foreach (var id in Select(catalog, rule))
            {
                var entry = RaceTroopBuilder.Armor.ArmorProtocol.WriteValues("Troop", rule.Armor!);
                entry.SetAttributeValue("id", id); entry.SetAttributeValue("race", rule.RaceId); armorXml.Add(entry);
            }
            new XDocument(armorXml).Save(Path.Combine(modulePath, "ModuleData", RaceTroopBuilder.Armor.ArmorProtocol.TroopFile));
        }
        module.Save(Path.Combine(modulePath, "SubModule.xml"));
        stylesheet.Save(Path.Combine(modulePath, "ModuleData", "rtb_troops.xslt"));
        new XDocument(new XElement("NPCCharacters")).Save(Path.Combine(modulePath, "ModuleData", "rtb_troops.xml"));
        Json.Save(Path.Combine(modulePath, "ModuleData", "rtb_manifest.json"), new { generator = "RaceTroopBuilder", generatorVersion = "0.2.0", project.ModuleId, project.Version });
        File.WriteAllText(Path.Combine(modulePath, "README.txt"), "Generated by RaceTroopBuilder\nLoad order (top to bottom):\n" + string.Join("\n", report.LoadOrder) +
            "\n\nRace assets are external dependencies. This package does not include them.\nOffline checks passed; in-game acceptance is required.\n");
        report.ModulePath = modulePath;
        report.FileHashes = HashFiles(modulePath);
        foreach (var dependency in report.LoadOrder.Where(x => x != project.ModuleId && !Discovery.OfficialIds.Contains(x)))
            report.DependencyHashes[dependency] = DependencyHashes(catalog.Modules[dependency]);
        Json.Save(Path.Combine(root, project.ModuleId + ".validation.json"), report);
        Json.Save(Path.Combine(root, project.ModuleId + ".project.json"), project);
        return report;
    }

    // XSLT interprets braces in literal attributes as expressions; preserve localization tokens.
    private static XElement EscapeLiteral(XElement original)
    {
        var copy = new XElement(original);
        foreach (var attribute in copy.DescendantsAndSelf().Attributes()) attribute.Value = attribute.Value.Replace("{", "{{").Replace("}", "}}");
        foreach (var comment in copy.DescendantNodes().OfType<XComment>().ToList())
            comment.ReplaceWith(new XElement(Xsl + "comment", comment.Value));
        foreach (var instruction in copy.DescendantNodes().OfType<XProcessingInstruction>().ToList())
            instruction.ReplaceWith(new XElement(Xsl + "processing-instruction", new XAttribute("name", instruction.Target), instruction.Data));
        return copy;
    }
    private static XElement Normalize(XElement original)
    {
        var copy = new XElement(original);
        copy.DescendantNodes().OfType<XText>().Where(x => string.IsNullOrWhiteSpace(x.Value)).Remove();
        foreach (var element in copy.DescendantsAndSelf()) if (!element.Nodes().Any()) element.RemoveNodes();
        return copy;
    }
    private static XDocument Apply(XslCompiledTransform transform, XDocument document)
    {
        using var stream = new MemoryStream();
        using (var writer = XmlWriter.Create(stream, transform.OutputSettings)) using (var reader = document.CreateReader()) transform.Transform(reader, writer);
        stream.Position = 0; return XDocument.Load(stream);
    }
    public static Dictionary<string, string> HashFiles(string directory) => Directory.EnumerateFiles(directory, "*", SearchOption.AllDirectories)
        .Order(StringComparer.Ordinal).ToDictionary(x => Path.GetRelativePath(directory, x).Replace('\\', '/'), x => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(x))).ToLowerInvariant());

    private static Dictionary<string, string> DependencyHashes(ModuleInfo module)
    {
        var files = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { Path.Combine(module.Path, "SubModule.xml") };
        var armor = Path.Combine(module.Path, "ModuleData", RaceTroopBuilder.Armor.ArmorProtocol.RaceFile);
        if (File.Exists(armor)) files.Add(armor);
        foreach (var folder in new[] { "ModuleData", "AssetPackages", "bin" })
        {
            var path = Path.Combine(module.Path, folder);
            if (Directory.Exists(path)) foreach (var file in Directory.EnumerateFiles(path, "*", SearchOption.AllDirectories)) files.Add(file);
        }
        return files.Order(StringComparer.Ordinal).ToDictionary(x => Path.GetRelativePath(module.Path, x).Replace('\\', '/'), HashFile);
    }
    private static string HashFile(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }

    public static string Package(string reportFile, string archivePath)
    {
        var report = ReadVerifiedReport(reportFile);
        archivePath = Path.GetFullPath(archivePath);
        if (File.Exists(archivePath)) throw new IOException("交付包已存在，请保留旧包并使用新文件名。");
        Directory.CreateDirectory(Path.GetDirectoryName(archivePath)!);
        using var archive = ZipFile.Open(archivePath, ZipArchiveMode.Create);
        foreach (var file in Directory.EnumerateFiles(report.ModulePath!, "*", SearchOption.AllDirectories))
            archive.CreateEntryFromFile(file, Path.GetFileName(report.ModulePath) + "/" + Path.GetRelativePath(report.ModulePath!, file).Replace('\\', '/'));
        archive.CreateEntryFromFile(reportFile, "checks/validation.json");
        return archivePath;
    }

    public static CheckReport ReadVerifiedReport(string path)
    {
        var report = Json.Read<CheckReport>(path);
        if (report.Status != "pass" || report.ModulePath == null) throw new InvalidDataException("构建报告未通过或没有模块路径。");
        var hashes = HashFiles(report.ModulePath);
        if (hashes.Count != report.FileHashes.Count || hashes.Any(x => !report.FileHashes.TryGetValue(x.Key, out var hash) || hash != x.Value))
            throw new InvalidDataException("模块文件已改变，与离线检查报告不一致；请重新构建。");
        return report;
    }

    public static object Install(string reportFile, string? requestedGame = null, string? backupRoot = null)
    {
        var report = ReadVerifiedReport(reportFile);
        var game = Discovery.FindGame(requestedGame);
        var descriptor = Discovery.ReadModule(report.ModulePath!);
        if (!IdPattern().IsMatch(descriptor.Id) || IsReserved(descriptor.Id)) throw new InvalidDataException("禁止覆盖原版或非法模块。");
        var modules = Path.Combine(game, "Modules");
        if (Discovery.ReadModule(Path.Combine(modules, "Native")).Version != report.GameVersion) throw new InvalidDataException("安装目标游戏版本与构建版本不同。");
        foreach (var id in report.LoadOrder.Where(x => x != descriptor.Id))
        {
            var dependencyPath = Discovery.Inside(modules, id);
            if (!File.Exists(Path.Combine(dependencyPath, "SubModule.xml"))) throw new InvalidDataException("种族或其他依赖尚未安装：" + id);
            var dependency = Discovery.ReadModule(dependencyPath);
            if (dependency.Id != id) throw new InvalidDataException("安装目录与依赖模块 ID 不符：" + id);
            if (!report.DependencyVersions.TryGetValue(id, out var version) || dependency.Version != version)
                throw new InvalidDataException("已安装依赖版本与构建时不同：" + id);
            if (report.DependencyHashes.TryGetValue(id, out var expected))
            {
                var installed = DependencyHashes(dependency);
                if (installed.Count != expected.Count || installed.Any(x => !expected.TryGetValue(x.Key, out var hash) || hash != x.Value))
                    throw new InvalidDataException("已安装种族依赖与构建来源不一致，请先安装匹配的依赖或改用已安装模块扫描：" + id);
            }
        }
        var target = Discovery.Inside(modules, descriptor.Id);
        string? backup = null;
        if (Directory.Exists(target))
        {
            var marker = Path.Combine(target, "ModuleData", "rtb_manifest.json");
            if (!File.Exists(marker) || !File.ReadAllText(marker).Contains("\"generator\": \"RaceTroopBuilder\"", StringComparison.Ordinal))
                throw new IOException("目标不是此工具生成的模块，拒绝覆盖：" + target);
            if (Discovery.ReadModule(target).Id != descriptor.Id) throw new IOException("目标 Module Id 不匹配。");
            var backups = Path.GetFullPath(backupRoot ?? Path.Combine(Path.GetDirectoryName(Path.GetFullPath(reportFile))!, "install-backups"));
            if (backups.StartsWith(target + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) || backups.Equals(target, StringComparison.OrdinalIgnoreCase))
                throw new IOException("备份目录不能位于安装目标内。");
            Directory.CreateDirectory(backups);
            backup = Path.Combine(backups, descriptor.Id + "-" + DateTimeOffset.Now.ToString("yyyyMMdd-HHmmss-fff") + ".zip");
            ZipFile.CreateFromDirectory(target, backup);
        }
        // Stage first. Rename only this generated module and restore it if the swap fails.
        var staging = Discovery.Inside(modules, descriptor.Id + ".rtb-stage-" + Guid.NewGuid().ToString("N"));
        var rollback = Discovery.Inside(modules, descriptor.Id + ".rtb-old-" + Guid.NewGuid().ToString("N"));
        var movedOld = false;
        try
        {
            CopyTree(report.ModulePath!, staging);
            if (!HashFiles(staging).OrderBy(x => x.Key).SequenceEqual(report.FileHashes.OrderBy(x => x.Key))) throw new IOException("安装暂存文件校验失败。");
            if (Directory.Exists(target)) { Directory.Move(target, rollback); movedOld = true; }
            Directory.Move(staging, target);
        }
        catch
        {
            if (movedOld && !Directory.Exists(target)) Directory.Move(rollback, target);
            throw;
        }
        finally
        {
            // Inside() verified this unique staging path is beneath the chosen Modules directory.
            // A failed installation must not leave another discoverable copy of the same module ID.
            if (Directory.Exists(staging)) Directory.Delete(staging, true);
        }
        if (movedOld) Directory.Delete(rollback, true);
        return new { status = "pass", modulePath = target, backup, loadOrder = report.LoadOrder, gameStarted = false };
    }
    private static void CopyTree(string source, string target)
    {
        Directory.CreateDirectory(target);
        foreach (var file in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
        {
            var destination = Discovery.Inside(target, Path.GetRelativePath(source, file));
            Directory.CreateDirectory(Path.GetDirectoryName(destination)!); File.Copy(file, destination);
        }
    }
}
