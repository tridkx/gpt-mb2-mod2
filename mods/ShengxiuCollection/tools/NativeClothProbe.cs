using TpacTool.Lib;
using System.Text.Json;
using System.Security.Cryptography;
var pkg=new AssetPackage(args[0],true,false);
var selected=args.Skip(1).ToHashSet();
// Diagnostic output only; never writes or patches the input package.
var dumpAt=Array.IndexOf(args,"--dump-segments");
if(dumpAt>=0) {
 var dir=Path.GetFullPath(args[dumpAt+1]);
 Directory.CreateDirectory(dir);
 foreach(var mm in pkg.Items.OfType<Metamesh>().Where(x=>selected.Contains(x.Name)))
 foreach(var s in mm.TypelessDataSegments.Where(s=>s.TypeGuid==new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e"))) {
  var data=(ExternalData)s.GetType().GetProperty("Data")!.GetValue(s)!;
  using var stream=File.Create(Path.Combine(dir,$"{mm.Name}_{s.OwnerGuid}.bin"));
  using var writer=new BinaryWriter(stream);
  data.WriteData(writer,s.UserData);
 }
}
var rows=pkg.Items.OfType<Metamesh>().Where(x=>selected.Contains(x.Name)).Select(mm=>new {
 mm.Name,mm.Guid,mm.ClothMetamesh,mm.ClothUint,mm.ClothString,body=mm.UnknownString,
 segments=mm.TypelessDataSegments.Select(s=>new{s.TypeGuid,s.OwnerGuid,s.ActualSize,s.UnknownUint,s.UnknownUlong}),
 meshes=mm.Meshes.Select(m=>{
  var v=m.VertexStream.Data;
  var ed=m.EditData?.Data;
  using var bytes=new MemoryStream();
  using(var writer=new BinaryWriter(bytes,System.Text.Encoding.UTF8,true)) {
   v.WriteData(writer,new Dictionary<object,object>{{VertexStreamData.KEY_HAS_QTANGENT,v.TangentTransform!=null}});
   foreach(var i in v.Indices)writer.Write(i);
  }
  return new {m.Name,m.Guid,m.Lod,m.Flags,m.UnknownFloat1,m.UnknownInt3,m.UnknownBool1,m.UnknownBool2,m.UnknownBool3,m.ClothingMaterial,
   vertices=v.Positions.Length,triangles=v.Indices.Length/3,m.SkinDataSize,m.UnknownInt2,
   geometry_hash=Convert.ToHexString(SHA256.HashData(bytes.ToArray())),
   alpha_min=v.Colors1.Min(c=>c.A),alpha_max=v.Colors1.Max(c=>c.A),
   alpha_zero_count=v.Colors1.Count(c=>c.A==0),alpha_active_count=v.Colors1.Count(c=>c.A>0),
   edit_positions=ed?.Positions.Length,edit_vertices=ed?.Vertices.Length,edit_faces=ed?.Faces.Length,
   edit_bones=ed?.Bones.Length,edit_alpha_min=ed?.Vertices.Min(x=>x.Color.A),edit_alpha_max=ed?.Vertices.Max(x=>x.Color.A)};
 })});
Console.WriteLine(JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true}));
