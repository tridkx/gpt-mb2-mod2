using TpacTool.Lib;
using System.Text.Json;
using System.Security.Cryptography;
var pkg=new AssetPackage(args[0],true,false);
var selected=args.Skip(1).ToHashSet();
var rows=pkg.Items.OfType<Metamesh>().Where(x=>selected.Contains(x.Name)).Select(mm=>new {
 mm.Name,mm.Guid,mm.ClothMetamesh,mm.ClothUint,mm.ClothString,body=mm.UnknownString,
 meshes=mm.Meshes.Select(m=>{
  var v=m.VertexStream.Data;
  using var bytes=new MemoryStream();
  using(var writer=new BinaryWriter(bytes,System.Text.Encoding.UTF8,true)) {
   v.WriteData(writer,new Dictionary<object,object>{{VertexStreamData.KEY_HAS_QTANGENT,v.TangentTransform!=null}});
   foreach(var i in v.Indices)writer.Write(i);
  }
  return new {m.Name,m.Guid,m.Lod,m.Flags,m.UnknownFloat1,m.UnknownInt3,m.UnknownBool1,m.UnknownBool2,m.UnknownBool3,m.ClothingMaterial,
   vertices=v.Positions.Length,triangles=v.Indices.Length/3,m.SkinDataSize,m.UnknownInt2,
   geometry_hash=Convert.ToHexString(SHA256.HashData(bytes.ToArray())),
   alpha_min=v.Colors1.Min(c=>c.A),alpha_max=v.Colors1.Max(c=>c.A),
   alpha_zero_count=v.Colors1.Count(c=>c.A==0),alpha_active_count=v.Colors1.Count(c=>c.A>0)};
 })});
Console.WriteLine(JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true}));
