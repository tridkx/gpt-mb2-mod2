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
        var cloth = m.Lod == 0 && recipe.TryGetProperty(baseName, out _);
        m.Flags = cloth ? new List<string>{"uses_cloth_simulation"} : new List<string>();
        if (cloth) {
            // Reader field names are unverified; no editor-option equivalence is claimed.
            m.UnknownFloat1=1f; m.UnknownInt3=120; m.UnknownBool1=true; m.UnknownBool2=false; m.UnknownBool3=false;
            m.ClothingMaterial=new ClothingMaterial {
                Name="mf2_limited_fabric", BendingStiffness=.85f, ShearingStiffness=.96f,
                StretchingStiffness=1f, AnchorStiffness=1f, Damping=.60f, Gravity=9.81f,
                LinearInertia=.16f, AirDragMultiplier=.12f, Wind=.06f,
                MaxLinearVelocity=5f, LinearVelocityMultiplier=.50f
            };
        }
    }
}
foreach (var asset in pkg.Items) {
    var field=asset.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
    field?.SetValue(asset,null);
}
pkg.Save(args[2]);
Console.WriteLine("Patched TianxiangMufeng LOD and limited cloth: "+args[2]);
