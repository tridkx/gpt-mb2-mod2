using System.Xml;
using System.Xml.Linq;

namespace RaceTroopBuilder.Core;

public static class Discovery
{
    public static readonly string[] OfficialIds = ["Native", "SandBoxCore", "Sandbox", "StoryMode", "BirthAndDeath", "CustomBattle", "Multiplayer"];
    private static readonly HashSet<string> Excluded = new(StringComparer.OrdinalIgnoreCase)
        { "build", "dist", "reports", "history", "backups", "input", "source", "tex", "tools", "AssetPackages", "bin", "obj", ".git" };

    public static string? FindWorkspace(string start)
    {
        for (var directory = new DirectoryInfo(Path.GetFullPath(start)); directory != null; directory = directory.Parent)
            if (Directory.Exists(Path.Combine(directory.FullName, "mods")) && File.Exists(Path.Combine(directory.FullName, "AGENTS.md")))
                return directory.FullName;
        return null;
    }

    public static string DefaultModRoot()
    {
        var workspace = FindWorkspace(Environment.CurrentDirectory) ?? FindWorkspace(AppContext.BaseDirectory);
        return Path.Combine(workspace ?? Environment.CurrentDirectory, "mods");
    }

    public static string FindGame(string? requested = null)
    {
        if (!string.IsNullOrWhiteSpace(requested))
        {
            var path = Path.GetFullPath(requested);
            if (!File.Exists(Path.Combine(path, "Modules", "Native", "SubModule.xml")))
                throw new DirectoryNotFoundException("游戏目录应包含 Modules/Native/SubModule.xml：" + path);
            return path;
        }
        var env = Environment.GetEnvironmentVariable("BANNERLORD_GAME_ROOT");
        if (!string.IsNullOrWhiteSpace(env)) return FindGame(env);
        var candidates = new List<string> { @"D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord" };
        foreach (var drive in DriveInfo.GetDrives().Where(x => x.IsReady && x.DriveType == DriveType.Fixed))
        {
            candidates.Add(Path.Combine(drive.RootDirectory.FullName, "SteamLibrary", "steamapps", "common", "Mount & Blade II Bannerlord"));
            candidates.Add(Path.Combine(drive.RootDirectory.FullName, "Program Files (x86)", "Steam", "steamapps", "common", "Mount & Blade II Bannerlord"));
        }
        var found = candidates.FirstOrDefault(x => File.Exists(Path.Combine(x, "Modules", "Native", "SubModule.xml")));
        return found ?? throw new DirectoryNotFoundException("未找到游戏。请指定 gameRoot / --game，或设置 BANNERLORD_GAME_ROOT。");
    }

    public static XDocument Xml(string path)
    {
        using var reader = XmlReader.Create(path, new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null });
        return XDocument.Load(reader);
    }

    public static string Inside(string root, string relative)
    {
        var fullRoot = Path.GetFullPath(root);
        if (Path.IsPathRooted(relative)) throw new InvalidDataException("资源入口必须使用模块相对路径：" + relative);
        var path = Path.GetFullPath(Path.Combine(fullRoot, relative.Replace('/', Path.DirectorySeparatorChar)));
        if (!path.StartsWith(fullRoot.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("资源入口越过模块目录：" + relative);
        return path;
    }

    public static ModuleInfo ReadModule(string path)
    {
        var root = Xml(Path.Combine(path, "SubModule.xml")).Root ?? throw new InvalidDataException("空 SubModule.xml");
        string Value(string key) => (string?)root.Element(key)?.Attribute("value") ?? "";
        var id = Value("Id");
        if (string.IsNullOrWhiteSpace(id)) throw new InvalidDataException("缺少 Module Id：" + path);
        return new(id, Value("Name"), Value("Version"), Path.GetFullPath(path),
            root.Element("DependedModules")?.Elements("DependedModule")
                .Where(x => !string.Equals((string?)x.Attribute("Optional"), "true", StringComparison.OrdinalIgnoreCase))
                .Select(x => (string?)x.Attribute("Id") ?? "").Where(x => x.Length > 0).ToList() ?? [], root);
    }

    public static IEnumerable<string> ModuleDirectories(string root)
    {
        if (!Directory.Exists(root)) throw new DirectoryNotFoundException("Mod 搜索目录不存在：" + root);
        var pending = new Stack<string>(); pending.Push(Path.GetFullPath(root));
        while (pending.Count > 0)
        {
            var path = pending.Pop();
            if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) continue;
            if (File.Exists(Path.Combine(path, "SubModule.xml"))) { yield return path; continue; }
            foreach (var child in Directory.EnumerateDirectories(path).OrderByDescending(x => x, StringComparer.Ordinal))
                if (!Excluded.Contains(Path.GetFileName(child))) pending.Push(child);
        }
    }

    public static IEnumerable<string> RegisteredFiles(ModuleInfo module, string kind)
    {
        foreach (var entry in module.Descriptor.Element("Xmls")?.Elements("XmlNode") ?? [])
        {
            var xmlName = entry.Element("XmlName");
            if ((string?)xmlName?.Attribute("id") != kind) continue;
            var games = entry.Element("IncludedGameTypes")?.Elements("GameType").Select(x => (string?)x.Attribute("value")).ToList();
            if (games is { Count: > 0 } && !games.Contains("Campaign") && !games.Contains("CampaignStoryMode")) continue;
            var relative = "ModuleData/" + ((string?)xmlName?.Attribute("path") ?? throw new InvalidDataException("缺少 XML path"));
            var path = Inside(module.Path, relative);
            if (Directory.Exists(path))
            {
                foreach (var file in Directory.EnumerateFiles(path, "*.xml", SearchOption.AllDirectories).Order(StringComparer.Ordinal)) yield return file;
            }
            else
            {
                if (!path.EndsWith(".xml", StringComparison.OrdinalIgnoreCase)) path += ".xml";
                if (!File.Exists(path)) throw new FileNotFoundException("注册的 XML 文件不存在", path);
                yield return path;
            }
        }
    }

    public static Catalog Scan(string? gameRoot = null, IEnumerable<string>? modRoots = null)
    {
        var catalog = new Catalog { GameRoot = FindGame(gameRoot) };
        catalog.ModRoots = (modRoots?.Any() == true ? modRoots : [DefaultModRoot()])!.Select(Path.GetFullPath).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        foreach (var id in OfficialIds)
        {
            var path = Path.Combine(catalog.GameRoot, "Modules", id);
            if (File.Exists(Path.Combine(path, "SubModule.xml"))) catalog.Modules[id] = ReadModule(path);
        }
        catalog.GameVersion = catalog.Modules["Native"].Version;
        foreach (var root in catalog.ModRoots)
        foreach (var path in ModuleDirectories(root))
        {
            try
            {
                var module = ReadModule(path);
                if (OfficialIds.Contains(module.Id)) continue;
                if (catalog.Modules.TryGetValue(module.Id, out var existing))
                {
                    if (!string.Equals(existing.Path, module.Path, StringComparison.OrdinalIgnoreCase))
                        catalog.Issues.Add(new("error", "duplicate_module", $"模块 ID 重复；请选择唯一来源：{existing.Path} / {module.Path}", module.Id));
                    continue;
                }
                catalog.Modules[module.Id] = module;
                ReadRaces(catalog, module);
            }
            catch (Exception e) when (e is IOException or XmlException or InvalidDataException)
            { catalog.Issues.Add(new("error", "module_scan", e.Message, path)); }
        }
        var chinese = Localization.ReadChinese(catalog.Modules.Values.Where(x => OfficialIds.Contains(x.Id)));
        foreach (var id in new[] { "Native", "SandBoxCore", "Sandbox", "StoryMode", "BirthAndDeath" })
        {
            if (!catalog.Modules.TryGetValue(id, out var module)) continue;
            foreach (var file in RegisteredFiles(module, "Items"))
                foreach (var item in Xml(file).Root?.Elements() ?? [])
                {
                    if (item.Name.LocalName is not ("Item" or "CraftedItem")) continue;
                    var itemId = (string?)item.Attribute("id");
                    if (itemId == null) continue;
                    var armor = item.Element("ItemComponent")?.Element("Armor");
                    catalog.Items[itemId] = new(itemId, DisplayName((string?)item.Attribute("name") ?? itemId),
                        (string?)item.Attribute("Type") ?? CraftedType((string?)item.Attribute("crafting_template") ?? ""), id,
                        (string?)item.Element("ItemComponent")?.Element("Weapon")?.Attribute("weapon_class") ?? "")
                        {
                            NameKey = Localization.Key((string?)item.Attribute("name") ?? ""),
                            NameZh = Localization.Chinese((string?)item.Attribute("name") ?? "", chinese),
                            EquipmentArmor = new()
                            {
                                Head = Math.Max(0, (int?)armor?.Attribute("head_armor") ?? 0),
                                Body = Math.Max(0, (int?)armor?.Attribute("body_armor") ?? 0),
                                Arms = Math.Max(0, (int?)armor?.Attribute("arm_armor") ?? 0),
                                Legs = Math.Max(0, (int?)armor?.Attribute("leg_armor") ?? 0)
                            }
                        };
                }
            foreach (var file in RegisteredFiles(module, "EquipmentRosters"))
                foreach (var roster in Xml(file).Root?.Elements("EquipmentRoster") ?? [])
                    if ((string?)roster.Attribute("id") is string setId) catalog.EquipmentSets[setId] = new(roster);
            foreach (var file in RegisteredFiles(module, "NPCCharacters"))
            {
                var document = Xml(file); catalog.TroopDocuments.Add((file, document));
                foreach (var npc in document.Root?.Elements("NPCCharacter") ?? [])
                {
                    var troopId = (string?)npc.Attribute("id");
                    if (troopId == null) continue;
                    // Include campaign soldiers and tavern mercenaries; exclude heroes and obsolete definitions.
                    if ((string?)npc.Attribute("occupation") is not ("Soldier" or "Mercenary") || (string?)npc.Attribute("is_hero") == "true"
                        || (string?)npc.Attribute("is_obsolete") == "true"
                        || ((string?)npc.Attribute("occupation") == "Mercenary" && (string?)npc.Attribute("is_hidden_encyclopedia") == "true")) continue;
                    catalog.Troops[troopId] = new(troopId, DisplayName((string?)npc.Attribute("name") ?? troopId),
                        Ref((string?)npc.Attribute("culture") ?? ""), (int?)npc.Attribute("level") ?? 0,
                        (bool?)npc.Attribute("is_female") ?? false, (bool?)npc.Attribute("is_basic_troop") ?? false,
                        npc.Element("upgrade_targets")?.Elements("upgrade_target").Select(x => Ref((string?)x.Attribute("id") ?? "")).ToList() ?? [], new(npc))
                        { NameKey = Localization.Key((string?)npc.Attribute("name") ?? ""), NameZh = Localization.Chinese((string?)npc.Attribute("name") ?? "", chinese) };
                }
            }
        }
        foreach (var module in catalog.Modules.Values.Where(x => !OfficialIds.Contains(x.Id)))
        {
            try
            {
                var defaults = RaceTroopBuilder.Armor.ArmorProtocol.ReadRaces(Path.Combine(module.Path, "ModuleData", RaceTroopBuilder.Armor.ArmorProtocol.RaceFile));
                foreach (var entry in defaults)
                {
                    var index = catalog.Races.FindIndex(x => x.ModuleId == module.Id && x.Id == entry.Key);
                    if (index < 0) throw new InvalidDataException("护甲引用未注册种族：" + entry.Key);
                    catalog.Races[index] = catalog.Races[index] with { DefaultArmor = entry.Value };
                }
            }
            catch (Exception e) when (e is InvalidDataException or XmlException or IOException)
            { catalog.Issues.Add(new("error", "race_armor", e.Message, module.Id)); }
        }
        return catalog;
    }

    private static void ReadRaces(Catalog catalog, ModuleInfo module)
    {
        var projectFile = Path.Combine(module.Path, "ModuleData", "project.mbproj");
        if (!File.Exists(projectFile)) return;
        foreach (var entry in Xml(projectFile).Root?.Elements("file") ?? [])
        {
            if ((string?)entry.Attribute("id") != "soln_skins") continue;
            var file = Inside(module.Path, (string?)entry.Attribute("name") ?? "");
            foreach (var race in Xml(file).Root?.Elements("race") ?? [])
            {
                var raceId = (string?)race.Attribute("id") ?? throw new InvalidDataException("种族缺少 ID：" + file);
                var skins = race.Elements("skin").Select(x => new SkinInfo((int?)x.Attribute("gender") ?? 0,
                    (string?)x.Attribute("mesh_maturity_type") ?? "adult", (string?)x.Attribute("monster") ?? "",
                    (string?)x.Attribute("skeleton") ?? "")).ToList();
                if (skins.Count == 0) catalog.Issues.Add(new("error", "empty_race", "种族没有 skin。", raceId));
                catalog.Races.Add(new(module.Id, raceId, module.Path, skins));
            }
        }
    }

    public static string Ref(string value) => value.Contains('.') ? value[(value.IndexOf('.') + 1)..] : value;
    public static string DisplayName(string value) => value.StartsWith('{') && value.Contains('}') ? value[(value.IndexOf('}') + 1)..] : value;
    private static string CraftedType(string template) => template switch
    {
        "OneHandedSword" or "OneHandedAxe" or "OneHandedMace" => "OneHandedWeapon",
        "TwoHandedSword" or "TwoHandedAxe" or "TwoHandedMace" => "TwoHandedWeapon",
        "ThrowingAxe" or "ThrowingKnife" or "Javelin" => "Thrown",
        _ => "Polearm"
    };
}
