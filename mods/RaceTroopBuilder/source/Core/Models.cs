using System.Text.Json;
using System.Text.Json.Serialization;
using System.Xml.Linq;

namespace RaceTroopBuilder.Core;

public static class Json
{
    public static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = false,
        WriteIndented = true,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };
    public static string Write<T>(T value) => JsonSerializer.Serialize(value, Options);
    public static T Read<T>(string path) => JsonSerializer.Deserialize<T>(File.ReadAllText(path), Options)
        ?? throw new InvalidDataException("JSON 文件为空。");
    public static void Save<T>(string path, T value)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        var temp = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        File.WriteAllText(temp, Write(value) + "\n", new System.Text.UTF8Encoding(false));
        File.Move(temp, path, true);
    }
}

public sealed class BuilderProject
{
    public int SchemaVersion { get; set; } = 1;
    public string ModuleId { get; set; } = "MyRaceTroops";
    public string ModuleName { get; set; } = "My Race Troops";
    public string Version { get; set; } = "v0.1.0";
    public string DisplayLanguage { get; set; } = "zh-CN";
    public string? GameRoot { get; set; }
    public List<string> ModRoots { get; set; } = [];
    public List<TroopRule> Rules { get; set; } = [];
}

public sealed class TroopRule
{
    public List<string> TroopIds { get; set; } = [];
    public List<string> RootIds { get; set; } = [];
    public string? Culture { get; set; }
    public string RaceModule { get; set; } = "";
    public string RaceId { get; set; } = "";
    public bool? IsFemale { get; set; }
    public int? Age { get; set; }
    public string FaceMode { get; set; } = "preserve";
    public bool StripArmor { get; set; }
    public ArmorSettings? Armor { get; set; }
    public string? Name { get; set; }
    // Null retains native equipment; an explicit list replaces battle equipment only.
    public List<Loadout>? BattleLoadouts { get; set; }
    public List<Loadout>? CivilianLoadouts { get; set; }
    // Missing keys retain the original skill; zero explicitly overrides it.
    public Dictionary<string, int>? Skills { get; set; }
}

public sealed class ArmorSettings : RaceTroopBuilder.Armor.ArmorValues
{
    public string Mode { get; set; } = "inherit";
    public new int Head { get => base.Head; set { base.Head = value; HeadSet = true; } }
    public new int Body { get => base.Body; set { base.Body = value; BodySet = true; } }
    public new int Arms { get => base.Arms; set { base.Arms = value; ArmsSet = true; } }
    public new int Legs { get => base.Legs; set { base.Legs = value; LegsSet = true; } }
    [JsonIgnore] public bool HeadSet { get; private set; }
    [JsonIgnore] public bool BodySet { get; private set; }
    [JsonIgnore] public bool ArmsSet { get; private set; }
    [JsonIgnore] public bool LegsSet { get; private set; }
}

public sealed class Loadout
{
    public Dictionary<string, string> Slots { get; set; } = new(StringComparer.Ordinal);
}

public sealed record Issue(string Severity, string Code, string Message, string? Subject = null);
public sealed class CheckReport
{
    public string Status => Issues.Any(x => x.Severity == "error") ? "fail" : "pass";
    public List<Issue> Issues { get; set; } = [];
    public List<string> Targets { get; set; } = [];
    public List<string> LoadOrder { get; set; } = [];
    public string GameVersion { get; set; } = "";
    public string? ModulePath { get; set; }
    public Dictionary<string, string> FileHashes { get; set; } = [];
    public Dictionary<string, string> DependencyVersions { get; set; } = [];
    public Dictionary<string, Dictionary<string, string>> DependencyHashes { get; set; } = [];
    public int TransformChecks { get; set; }
    public string RuntimeTesting { get; set; } = "由用户在游戏内验收；离线通过不代表实机通过。";
}

public sealed record ModuleInfo(string Id, string Name, string Version, string Path,
    List<string> Dependencies, XElement Descriptor);
public sealed record SkinInfo(int Gender, string Maturity, string Monster, string Skeleton);
public sealed record RaceInfo(string ModuleId, string Id, string ModulePath, List<SkinInfo> Skins)
{
    public RaceTroopBuilder.Armor.ArmorValues? DefaultArmor { get; init; }
    public string Label => $"{Id}  [{ModuleId}]";
}
public sealed record ItemInfo(string Id, string Name, string Type, string ModuleId, string WeaponClass = "")
{
    public string NameEn => Name;
    public string NameZh { get; init; } = "";
    public string NameKey { get; init; } = "";
    public string Language { get; set; } = "zh-CN";
    public string DisplayName => Language == "zh-CN" && NameZh.Length > 0 ? NameZh : NameEn;
    public string SearchText => $"{Id} {NameEn} {NameZh} {Type}";
    public string Label => Id.Length == 0 ? "（空槽）" : $"{Id} · {DisplayName} ({Type})";
}
public sealed record TroopInfo(string Id, string Name, string Culture, int Level, bool IsFemale,
    bool IsBasicTroop, List<string> Upgrades, XElement Element)
{
    public string NameEn => Name;
    public string NameZh { get; init; } = "";
    public string NameKey { get; init; } = "";
    public string DisplayName(string language) => language == "zh-CN" && NameZh.Length > 0 ? NameZh : NameEn;
    public string SearchText => $"{Id} {NameEn} {NameZh} {Culture}";
    public string Label => $"{Name} [{Id}] · Lv{Level}";
}

public sealed class Catalog
{
    public string GameRoot { get; set; } = "";
    public string GameVersion { get; set; } = "";
    public List<string> ModRoots { get; set; } = [];
    public Dictionary<string, ModuleInfo> Modules { get; } = new(StringComparer.Ordinal);
    public List<RaceInfo> Races { get; } = [];
    public Dictionary<string, TroopInfo> Troops { get; } = new(StringComparer.Ordinal);
    public Dictionary<string, ItemInfo> Items { get; } = new(StringComparer.Ordinal);
    public Dictionary<string, XElement> EquipmentSets { get; } = new(StringComparer.Ordinal);
    public List<(string Path, XDocument Document)> TroopDocuments { get; } = [];
    public List<Issue> Issues { get; } = [];
}
