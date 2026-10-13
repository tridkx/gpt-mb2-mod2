using TpacTool.Lib;
using System.Text.Json;
var type=new Guid("af41613e-bd4d-46ec-8284-debb56c042dc");
var outdir=Path.GetFullPath(args[1]);Directory.CreateDirectory(outdir);
var rows=new List<object>();int count=0;
foreach(var file in Directory.EnumerateFiles(args[0],"*.tpac",SearchOption.AllDirectories)) {
 try {
 var pkg=new AssetPackage(file,true,false);
 foreach(var mm in pkg.Items.OfType<Metamesh>()) {
 if(mm.ClothMetamesh==Guid.Empty&&!mm.TypelessDataSegments.Any(s=>s.TypeGuid==type))continue;
 var proxy=pkg.Items.OfType<Metamesh>().FirstOrDefault(x=>x.Guid==mm.ClothMetamesh);
 var segments=new List<object>();
 foreach(var s in mm.TypelessDataSegments.Where(s=>s.TypeGuid==type)) {
  var data=(ExternalData)s.GetType().GetProperty("Data")!.GetValue(s)!;
  var path=Path.Combine(outdir,mm.Name+"_"+s.OwnerGuid+".map.bin");
  using var stream=File.Create(path);using var writer=new BinaryWriter(stream);data.WriteData(writer,s.UserData);
  segments.Add(new{s.OwnerGuid,s.ActualSize,path});
 }
 rows.Add(new{file,mm.Name,mm.Guid,mm.ClothMetamesh,mm.ClothUint,mm.ClothString,body=mm.UnknownString,proxyName=proxy?.Name,proxyMeshes=proxy?.Meshes.Select(m=>new{m.Name,m.Guid,m.Lod,m.Flags,vertices=m.VertexStream.Data.Positions.Length}),segments,meshes=mm.Meshes.Select(m=>new{m.Name,m.Guid,m.Lod,m.Flags,vertices=m.VertexStream.Data.Positions.Length})});
 Console.WriteLine(mm.Name+" proxy="+mm.ClothMetamesh+" maps="+segments.Count);
 if(++count>=8)break;
 }
 if(count>=8)break;
 }catch(Exception e){Console.WriteLine("READ_ERROR "+file+" "+e.Message);}
}
File.WriteAllText(Path.Combine(outdir,"native_mapping_samples.json"),JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true}));
