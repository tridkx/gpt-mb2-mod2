using TpacTool.Lib;
using System.Text.Json;
using System.Text.RegularExpressions;
var package=new AssetPackage(args[0],true,false);
using var geometry=JsonDocument.Parse(File.ReadAllText(args[2]));
var rows=geometry.RootElement.EnumerateArray().ToDictionary(x=>x.GetProperty("name").GetString()!);
foreach(var mesh in package.Items.OfType<Metamesh>()) {
    if(!mesh.Name.StartsWith("wdr_"))throw new InvalidDataException("Unexpected mesh namespace");
    mesh.UnknownString=mesh.Name=="wdr_canglan_body"?"wdr_canglan_collision":"";
    foreach(var group in mesh.Meshes) {
        var match=Regex.Match(group.Name,@"\.lod(\d+)");
        group.Lod=match.Success?int.Parse(match.Groups[1].Value):0;
        bool cloth=rows[group.Name].GetProperty("cloth").GetBoolean();
        group.Flags=cloth?new List<string>{"uses_cloth_simulation","force_enable_cloth"}:new List<string>();
        if(cloth) {
            group.UnknownFloat1=1;group.UnknownInt3=120;group.UnknownBool1=true;group.UnknownBool2=false;group.UnknownBool3=true;
            group.ClothingMaterial=new ClothingMaterial{Name="wdr_canglan_fabric",BendingStiffness=.22f,ShearingStiffness=.9f,StretchingStiffness=1,AnchorStiffness=1,Damping=.65f,Gravity=9.81f,LinearInertia=.12f,AirDragMultiplier=.08f,Wind=.025f,MaxLinearVelocity=4,LinearVelocityMultiplier=.5f};
        }
    }
}
foreach(var asset in package.Items)asset.GetType().BaseType?.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(asset,null);
package.Save(args[1]);
