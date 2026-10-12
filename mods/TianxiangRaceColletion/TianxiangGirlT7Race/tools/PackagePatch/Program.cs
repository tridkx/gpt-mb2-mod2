using TpacTool.Lib;
using System.Text.RegularExpressions;
using System.Text.Json;
var p=new AssetPackage(args[0],true,false);
using var geometry=JsonDocument.Parse(File.ReadAllText(args[2]));
var rows=geometry.RootElement.EnumerateArray().ToDictionary(x=>x.GetProperty("name").GetString());
foreach(var mesh in p.Items.OfType<Metamesh>()) {
 if(!mesh.Name.StartsWith("txgirl7_")) throw new InvalidDataException("Unexpected namespace");
 mesh.UnknownString=mesh.Name=="txgirl7_body" && rows.Values.Any(r=>r.TryGetProperty("cloth",out var c)&&c.GetBoolean())?"txgirl7_leg_collision":"";
 foreach(var g in mesh.Meshes) {
  var m=Regex.Match(g.Name,@"\.lod(\d+)");g.Lod=m.Success?int.Parse(m.Groups[1].Value):0;
  var name=Regex.Replace(g.Name,@"\.b\d+$","");
  bool cloth=rows[name].TryGetProperty("cloth",out var enabled)&&enabled.GetBoolean();
  g.Flags=cloth?new List<string>{"uses_cloth_simulation","force_enable_cloth"}:new List<string>();
  if(cloth){
   g.UnknownFloat1=1;g.UnknownInt3=120;g.UnknownBool1=true;g.UnknownBool2=false;g.UnknownBool3=true;
   g.ClothingMaterial=new ClothingMaterial{Name="txgirl7_skirt_silk",BendingStiffness=.20f,ShearingStiffness=.9f,StretchingStiffness=1,AnchorStiffness=1,Damping=.70f,Gravity=9.81f,LinearInertia=.12f,AirDragMultiplier=.08f,Wind=.025f,MaxLinearVelocity=4,LinearVelocityMultiplier=.5f};
  }
 }
}
foreach(var a in p.Items) a.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(a,null);
p.Save(args[1]);
