using TpacTool.Lib;
using System.Text.Json;
using System.Text.RegularExpressions;
var package=new AssetPackage(args[0],true,false);
using var geo=JsonDocument.Parse(File.ReadAllText(args[2]));
var rows=geo.RootElement.EnumerateArray().ToDictionary(r=>r.GetProperty("name").GetString()!);
foreach(var mesh in package.Items.OfType<Metamesh>()) {
 if(!mesh.Name.StartsWith("emilie_"))throw new InvalidDataException("Unexpected namespace");
 mesh.UnknownString=mesh.Name=="emilie_body"||mesh.Name=="emilie_cloth_proxy"?"emilie_collision":"";
 foreach(var group in mesh.Meshes) {
  var match=Regex.Match(group.Name,@"\.lod(\d+)");group.Lod=match.Success?int.Parse(match.Groups[1].Value):0;
  bool cloth=rows[group.Name].TryGetProperty("cloth",out var value)&&value.GetBoolean();
  group.Flags=cloth?new List<string>{"uses_cloth_simulation","force_enable_cloth"}:new List<string>();
  if(cloth) {
   group.UnknownFloat1=1;group.UnknownInt3=120;group.UnknownBool1=true;group.UnknownBool2=false;group.UnknownBool3=true;
   group.ClothingMaterial=new ClothingMaterial{Name="emilie_trail_fabric",BendingStiffness=.18f,ShearingStiffness=.9f,StretchingStiffness=1,AnchorStiffness=.6f,Damping=.88f,Gravity=9.81f,LinearInertia=.08f,AirDragMultiplier=.04f,Wind=.015f,MaxLinearVelocity=4,LinearVelocityMultiplier=1};
  }
 }
}
foreach(var asset in package.Items)asset.GetType().BaseType?.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(asset,null);
package.Save(args[1]);
