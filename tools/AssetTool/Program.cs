using TpacTool.Lib;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.RegularExpressions;
var options = new JsonSerializerOptions { WriteIndented = true };
var pkg = new AssetPackage(args[1], true, false);
if(args[0]=="inspect") {
 var meshes=pkg.Items.OfType<Metamesh>().Where(m=>args.Length<3 || m.Name==args[2]).Select(mm=>new {
 mm.Name,mm.UnknownString,mm.ClothMetamesh,mm.ClothUint,mm.ClothString,
 meshes=mm.Meshes.Select(m=>new {m.Name,m.Lod,m.Flags,m.UnknownFloat1,m.UnknownInt3,m.UnknownBool1,m.UnknownBool2,m.UnknownBool3,m.ClothingMaterial})});
 Console.WriteLine(JsonSerializer.Serialize(meshes,options));
} else if(args[0]=="patch") {
 using var spec=JsonDocument.Parse(File.ReadAllText(args[2]));
 foreach(var mm in pkg.Items.OfType<Metamesh>()) {
  var recipe=spec.RootElement.GetProperty(mm.Name);
  mm.UnknownString=recipe.GetProperty("body").GetString();
  foreach(var m in mm.Meshes) {
   var match=Regex.Match(m.Name,@"\.lod(\d+)");
   m.Lod=match.Success?int.Parse(match.Groups[1].Value):0;
   bool cloth=m.Lod==0 && recipe.TryGetProperty("clothGroups",out var cg) && cg.EnumerateArray().Any(v=>m.Name.Contains(v.GetString()));
   if(cloth) {
    m.Flags=new List<string>{"uses_cloth_simulation"};
    m.UnknownFloat1=1f;m.UnknownInt3=240;m.UnknownBool1=true;m.UnknownBool2=false;m.UnknownBool3=false;
    m.ClothingMaterial=new ClothingMaterial {Name="tx5_conservative",BendingStiffness=0.72f,ShearingStiffness=0.90f,StretchingStiffness=1f,AnchorStiffness=1f,Damping=0.45f,Gravity=9.81f,LinearInertia=0.35f,AirDragMultiplier=0.18f,Wind=0.20f,MaxLinearVelocity=8f,LinearVelocityMultiplier=0.7f};
   } else {m.Flags=new List<string>();}
  }
 }
 // Every modified metadata block must be serialized rather than reusing source bytes.
 foreach(var a in pkg.Items) {
  var field=a.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
  if(field!=null)field.SetValue(a,null);
 }
 pkg.Save(args[3]);
 Console.WriteLine("Saved "+args[3]);
}
