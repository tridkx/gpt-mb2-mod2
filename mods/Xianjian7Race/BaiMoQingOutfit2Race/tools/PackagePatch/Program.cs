using TpacTool.Lib;
using System.Text.RegularExpressions;
using System.Text.Json;
var package = new AssetPackage(args[0], true, false);
using var geometry=JsonDocument.Parse(File.ReadAllText(args[2]));
var rows=geometry.RootElement.EnumerateArray().ToDictionary(x=>x.GetProperty("name").GetString()!);
foreach (var mesh in package.Items.OfType<Metamesh>()) {
    if (!mesh.Name.StartsWith("bmq2_", StringComparison.Ordinal))
        throw new InvalidDataException("Unexpected asset namespace");
    mesh.UnknownString = mesh.Name == "bmq2_body" ? "bmq2_collision" : "";
    foreach (var group in mesh.Meshes) {
        var match = Regex.Match(group.Name, @"\.lod(\d+)");
        group.Lod = match.Success ? int.Parse(match.Groups[1].Value) : 0;
        if (group.Lod is < 0 or > 3) throw new InvalidDataException("Invalid LOD");
        var originalName=Regex.Replace(group.Name,@"\.b\d+$","");
        bool cloth=rows[originalName].TryGetProperty("cloth",out var enabled)&&enabled.GetBoolean()
            &&group.VertexStream.Data.Colors1.Any(c=>c.A>0);
        group.Flags = cloth ? new List<string>{"uses_cloth_simulation","force_enable_cloth"}:new List<string>();
        if(cloth) {
            bool hair=rows[originalName].GetProperty("kind").GetString()=="hair";
            group.UnknownFloat1=1;group.UnknownInt3=120;group.UnknownBool1=true;group.UnknownBool2=false;group.UnknownBool3=true;
            group.ClothingMaterial=new ClothingMaterial{Name=hair?"bmq2_soft_fibers":"bmq2_silk",BendingStiffness=hair?.15f:.25f,ShearingStiffness=.9f,StretchingStiffness=1,AnchorStiffness=1,Damping=.70f,Gravity=9.81f,LinearInertia=.12f,AirDragMultiplier=.08f,Wind=.025f,MaxLinearVelocity=4,LinearVelocityMultiplier=.5f};
        }
    }
}
foreach (var asset in package.Items) {
    var field = asset.GetType().BaseType.GetField("_rawMetadata", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
    field?.SetValue(asset, null);
}
package.Save(args[1]);
Console.WriteLine("Yue Qingshu LOD metadata saved: " + args[1]);
