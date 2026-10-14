using TpacTool.Lib;
using System.Text.Json;
using System.Text.RegularExpressions;
var pkg=new AssetPackage(args[0],true,false);
using var geo=JsonDocument.Parse(File.ReadAllText(args[2]));
var rows=geo.RootElement.EnumerateArray().ToDictionary(r=>r.GetProperty("name").GetString()!);
var prefix=args[3];var collision=args[4];
foreach(var material in pkg.Items.OfType<Material>()) {
 if(material.Flags.Contains("dont_draw_to_gbuffer")&&material.Flags.Contains("alpha_blend_sort"))material.ExtraMaterialSettings.RenderOrder=1;
}
foreach(var mesh in pkg.Items.OfType<Metamesh>()) {
 if(!mesh.Name.StartsWith(prefix+"_"))throw new InvalidDataException("Unexpected namespace");
 mesh.UnknownString=mesh.Name==prefix+"_body"||mesh.Name==prefix+"_cloth_proxy"?collision:"";
 foreach(var group in mesh.Meshes) {
  var match=Regex.Match(group.Name,@"\.lod(\d+)");group.Lod=match.Success?int.Parse(match.Groups[1].Value):0;
  var sourceName=Regex.Replace(group.Name,@"\.b\d+$","");
  bool cloth=rows[sourceName].TryGetProperty("cloth",out var value)&&value.GetBoolean();
  group.Flags=cloth?new List<string>{"uses_cloth_simulation","force_enable_cloth"}:new List<string>();
  if(cloth) {
   group.UnknownFloat1=1;group.UnknownInt3=120;group.UnknownBool1=true;group.UnknownBool2=false;group.UnknownBool3=true;
   group.ClothingMaterial=new ClothingMaterial{Name=prefix+"_hair_fabric",BendingStiffness=.15f,ShearingStiffness=.9f,StretchingStiffness=1,AnchorStiffness=.6f,Damping=.9f,Gravity=9.81f,LinearInertia=.08f,AirDragMultiplier=.04f,Wind=.015f,MaxLinearVelocity=4,LinearVelocityMultiplier=1};
  }
 }
}
foreach(var asset in pkg.Items)asset.GetType().BaseType?.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(asset,null);
pkg.Save(args[1]);Console.WriteLine("Own package metadata saved: "+args[1]);
