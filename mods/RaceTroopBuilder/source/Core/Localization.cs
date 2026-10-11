using System.Xml.Linq;

namespace RaceTroopBuilder.Core;

public static class Localization
{
    public static string Key(string raw) => raw.StartsWith("{=", StringComparison.Ordinal) && raw.Contains('}') ? raw[2..raw.IndexOf('}')] : "";
    public static string Chinese(string raw, IReadOnlyDictionary<string, string> strings) => strings.GetValueOrDefault(Key(raw)) ?? "";
    public static Dictionary<string, string> ReadChinese(IEnumerable<ModuleInfo> modules)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var module in modules)
        {
            var directory = Path.Combine(module.Path, "ModuleData", "Languages");
            var manifest = Path.Combine(directory, "CNs", "language_data.xml");
            if (!File.Exists(manifest)) continue;
            foreach (var entry in Discovery.Xml(manifest).Root?.Elements("LanguageFile") ?? [])
            {
                var relative = (string?)entry.Attribute("xml_path");
                if (relative == null) continue;
                var path = Discovery.Inside(directory, relative);
                if (!File.Exists(path)) continue;
                foreach (var text in Discovery.Xml(path).Descendants("string"))
                    if ((string?)text.Attribute("id") is string id && (string?)text.Attribute("text") is string value) result[id] = value;
            }
        }
        return result;
    }
}
