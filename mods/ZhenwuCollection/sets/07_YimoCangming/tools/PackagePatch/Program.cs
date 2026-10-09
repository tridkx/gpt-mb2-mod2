using TpacTool.Lib;
using System.Text.Json;
using System.Text.RegularExpressions;
var pkg = new AssetPackage(args[0], true, false);
using var spec = JsonDocument.Parse(File.ReadAllText(args[1]));
foreach (var mm in pkg.Items.OfType<Metamesh>()) {
    var recipe = spec.RootElement.GetProperty(mm.Name);
    mm.UnknownString = "human_body";
    foreach (var m in mm.Meshes) {
        var match = Regex.Match(m.Name, @"\.lod(\d+)");
        m.Lod = match.Success ? int.Parse(match.Groups[1].Value) : 0;
        var baseName = Regex.Replace(m.Name, @"\.b\d+$", "");
        var cloth = recipe.TryGetProperty(baseName, out var settings);
        m.Flags = cloth ? new List<string>{"uses_cloth_simulation"} : new List<string>();
        if (cloth) {
            // Reader field names are unverified; no editor-option equivalence is claimed.
            var profile=settings.GetProperty("profile");
            m.Flags=profile.GetProperty("flags").EnumerateArray().Select(v=>v.GetString()).ToList();
            m.UnknownFloat1=profile.GetProperty("UnknownFloat1").GetSingle(); m.UnknownInt3=120; m.UnknownBool1=true; m.UnknownBool2=false; m.UnknownBool3=profile.GetProperty("UnknownBool3").GetBoolean();
            m.ClothingMaterial=JsonSerializer.Deserialize<ClothingMaterial>(profile.GetProperty("material").GetRawText())!;
        }
    }
}
foreach (var asset in pkg.Items) {
    var field=asset.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
    field?.SetValue(asset,null);
}
pkg.Save(args[2]);
Console.WriteLine("Patched Zhenwu Yimo LOD and limited cloth: "+args[2]);
