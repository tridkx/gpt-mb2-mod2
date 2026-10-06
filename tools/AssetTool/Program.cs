using TpacTool.Lib;
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Security.Cryptography;
var options = new JsonSerializerOptions { WriteIndented = true };
var pkg = new AssetPackage(args[1], true, false);
if(args[0]=="inspect") {
 var meshes=pkg.Items.OfType<Metamesh>().Where(m=>args.Length<3 || m.Name==args[2]).Select(mm=>new {
 mm.Name,mm.UnknownString,mm.ClothMetamesh,mm.ClothUint,mm.ClothString,
 meshes=mm.Meshes.Select(m=>new {m.Name,m.Lod,m.Flags,m.MaterialFlags,m.UnknownFloat1,m.UnknownInt3,m.UnknownBool1,m.UnknownBool2,m.UnknownBool3,m.ClothingMaterial})});
 Console.WriteLine(JsonSerializer.Serialize(meshes,options));
} else if(args[0]=="materials") {
 var materials=pkg.Items.OfType<Material>().Where(m=>args.Length<3 || m.Name.Contains(args[2]) || m.ShaderMaterialFlags.Contains(args[2])).Select(m=>new {
 m.Name,m.Flags,m.VertexLayoutFlags,m.BlendMode,m.AlphaTest,m.ShaderMaterialFlags});
 Console.WriteLine(JsonSerializer.Serialize(materials,options));
} else if(args[0]=="visibility") {
 var materials=pkg.Items.OfType<Material>().Select(m=>new {m.Name,m.Guid,m.BlendMode,m.AlphaTest,m.ShaderMaterialFlags});
 var meshes=pkg.Items.OfType<Metamesh>().SelectMany(mm=>mm.Meshes.Select(m=> {
  var v=m.VertexStream.Data;
  var colors=v.Colors1.SelectMany(c=>new byte[]{c.R,c.G,c.B,c.A}).ToArray();
  using var vertexBytes=new MemoryStream();
  using(var writer=new BinaryWriter(vertexBytes,System.Text.Encoding.UTF8,true))
   v.WriteData(writer,new Dictionary<object,object>{{VertexStreamData.KEY_HAS_QTANGENT,v.TangentTransform!=null}});
  var clothMetadata=JsonSerializer.SerializeToUtf8Bytes(new {
   mm.UnknownString,mm.ClothMetamesh,mm.ClothUint,mm.ClothString,
   m.MaterialFlags,m.UnknownFloat1,m.UnknownInt3,m.UnknownBool1,m.UnknownBool2,m.UnknownBool3,m.ClothingMaterial});
  return new {m.Name,m.Lod,m.Flags,Material=m.Material.Guid,Vertices=v.Positions.Length,
   AlphaMin=v.Colors1.Min(c=>c.A),AlphaMax=v.Colors1.Max(c=>c.A),ColorsSHA256=Convert.ToHexString(SHA256.HashData(colors)),
   VertexStreamSHA256=Convert.ToHexString(SHA256.HashData(vertexBytes.ToArray())),
   ClothMetadataSHA256=Convert.ToHexString(SHA256.HashData(clothMetadata))};
 }));
 Console.WriteLine(JsonSerializer.Serialize(new {materials,meshes},options));
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
