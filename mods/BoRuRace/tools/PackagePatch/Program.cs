using TpacTool.Lib;
using System.Text.RegularExpressions;
var package = new AssetPackage(args[0], true, false);
var lens=package.Items.OfType<Material>().Single(m=>m.Name=="boru_race_glass");
if (!lens.Flags.Contains("dont_draw_to_gbuffer") || !lens.Flags.Contains("no_modify_depth_buffer"))
    throw new InvalidDataException("Lens must use forward transparency without writing opaque depth");
lens.ExtraMaterialSettings.RenderOrder=1;
foreach (var mesh in package.Items.OfType<Metamesh>()) {
    if (!mesh.Name.StartsWith("boru_race_", StringComparison.Ordinal))
        throw new InvalidDataException("Unexpected asset namespace");
    mesh.UnknownString = mesh.Name == "boru_race_body" ? "human_body" : "";
    foreach (var group in mesh.Meshes) {
        var match = Regex.Match(group.Name, @"\.lod(\d+)");
        group.Lod = match.Success ? int.Parse(match.Groups[1].Value) : 0;
        if (group.Lod is < 0 or > 3) throw new InvalidDataException("Invalid LOD");
        group.Flags = new List<string>();
    }
}
foreach (var asset in package.Items) {
    var field = asset.GetType().BaseType.GetField("_rawMetadata", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
    field?.SetValue(asset, null);
}
package.Save(args[1]);
Console.WriteLine("BoRu LOD metadata saved: " + args[1]);
