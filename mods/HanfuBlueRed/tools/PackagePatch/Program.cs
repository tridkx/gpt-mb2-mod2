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
        var cloth = m.Lod == 0 && recipe.TryGetProperty(baseName, out var settings);
        m.Flags = cloth ? new List<string>{"uses_cloth_simulation"} : new List<string>();
        if (cloth) {
            m.UnknownFloat1=1f; m.UnknownInt3=120; m.UnknownBool1=true; m.UnknownBool2=false; m.UnknownBool3=false;
            m.ClothingMaterial=new ClothingMaterial {
                Name="hbr_limited_fabric", BendingStiffness=.78f, ShearingStiffness=.94f,
                StretchingStiffness=1f, AnchorStiffness=1f, Damping=.55f, Gravity=9.81f,
                LinearInertia=.20f, AirDragMultiplier=.12f, Wind=.10f,
                MaxLinearVelocity=6f, LinearVelocityMultiplier=.55f
            };
        }
    }
}
foreach (var asset in pkg.Items) {
    var field=asset.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
    field?.SetValue(asset,null);
}
pkg.Save(args[2]);
Console.WriteLine("Patched Hanfu LOD and cloth metadata: "+args[2]);
