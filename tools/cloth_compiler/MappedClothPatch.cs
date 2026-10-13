using TpacTool.Lib;
using System.Text.Json;
using System.Security.Cryptography;
if(args.Length==5&&args[0]=="--inspect") {
 var package=new AssetPackage(args[1],true,false);var output=Path.GetFullPath(args[4]);Directory.CreateDirectory(output);
 var rows=new List<object>();
 foreach(var mm in package.Items.OfType<Metamesh>().Where(m=>m.Name==args[2]||m.Name==args[3])) {
  var segments=new List<object>();
  foreach(var s in mm.TypelessDataSegments.Where(s=>s.TypeGuid==new Guid("af41613e-bd4d-46ec-8284-debb56c042dc")||s.TypeGuid==new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e"))) {
   var data=(ExternalData)s.GetType().GetProperty("Data")!.GetValue(s)!;
   using var stream=new MemoryStream();using(var writer=new BinaryWriter(stream,System.Text.Encoding.UTF8,true))data.WriteData(writer,s.UserData);
   var raw=stream.ToArray();var path=Path.Combine(output,s.OwnerGuid+"_"+s.TypeGuid+".bin");File.WriteAllBytes(path,raw);
   segments.Add(new{s.OwnerGuid,s.TypeGuid,path,sha256=Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant()});
  }
  rows.Add(new{mm.Name,mm.Guid,mm.ClothMetamesh,body=mm.UnknownString,segments,meshes=mm.Meshes.Select(m=>new{m.Name,m.Guid,m.Lod,m.Flags,vertices=m.VertexStream.Data.Positions.Length,m.ClothingMaterial})});
 }
 File.WriteAllText(Path.Combine(output,"inspection.json"),JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true}));
 return;
}
if(args.Length!=6)throw new Exception("input output mapping_manifest body_name proxy_name native_template_tpac required");
if(Path.GetFullPath(args[0])==Path.GetFullPath(args[1]))throw new Exception("Preserve input");
var pkg=new AssetPackage(args[0],true,false);
var body=pkg.Items.OfType<Metamesh>().Single(m=>m.Name==args[3]);
var proxy=pkg.Items.OfType<Metamesh>().Single(m=>m.Name==args[4]);
if(proxy.Meshes.Count!=1||proxy.Meshes[0].Lod!=0)throw new Exception("One shared LOD0 proxy required");
var template=new AssetPackage(args[5],true,false);
var mapType=new Guid("af41613e-bd4d-46ec-8284-debb56c042dc");
var clothType=new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e");
var descriptor=template.Items.OfType<Metamesh>().SelectMany(m=>m.TypelessDataSegments).First(s=>s.TypeGuid==mapType);
using var manifest=JsonDocument.Parse(File.ReadAllText(args[2]));
var touched=new HashSet<Guid>();
foreach(var row in manifest.RootElement.EnumerateArray()) {
 var guid=row.GetProperty("guid").GetGuid();var mesh=body.Meshes.Single(m=>m.Guid==guid);
 if(!mesh.Flags.Contains("uses_cloth_simulation"))throw new Exception("Mapping outside active render mesh");
 foreach(var vertex in row.GetProperty("unmapped_vertices").EnumerateArray()) {
  var i=vertex.GetInt32();var color=mesh.VertexStream.Data.Colors1[i];color.A=0;mesh.VertexStream.Data.Colors1[i]=color;
 }
 mesh.VertexStream.MarkLongLive();
 var raw=File.ReadAllBytes(row.GetProperty("path").GetString()!);
 if(Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant()!=row.GetProperty("sha256").GetString())throw new Exception("Mapping hash mismatch");
 var data=new ExternalData(mapType);using(var reader=new BinaryReader(new MemoryStream(raw)))data.ReadData(reader,new Dictionary<object,object>(),raw.Length);
 body.TypelessDataSegments.RemoveAll(s=>s.OwnerGuid==guid&&(s.TypeGuid==mapType||s.TypeGuid==clothType));
 var loader=new ExternalLoader<ExternalData>(data){OwnerGuid=guid,UnknownUint=descriptor.UnknownUint,UnknownUlong=descriptor.UnknownUlong};
 foreach(var pair in descriptor.UserData)loader.UserData[pair.Key]=pair.Value;
 body.TypelessDataSegments.Add(loader);touched.Add(guid);
}
if(!body.Meshes.Where(m=>m.Flags.Contains("uses_cloth_simulation")).All(m=>touched.Contains(m.Guid)))throw new Exception("Unmapped active render mesh");
body.ClothMetamesh=proxy.Guid;body.ClothUint=0;body.ClothString="";
proxy.UnknownString=body.UnknownString;proxy.ClothMetamesh=Guid.Empty;
var driver=proxy.Meshes[0];driver.Flags=new List<string>{"uses_cloth_simulation","force_enable_cloth"};driver.UnknownFloat1=1;driver.UnknownInt3=120;driver.UnknownBool1=true;driver.UnknownBool2=false;driver.UnknownBool3=true;
driver.ClothingMaterial=new ClothingMaterial{Name=args[4]+"_soft_driver",BendingStiffness=.08f,ShearingStiffness=.9f,StretchingStiffness=1,AnchorStiffness=.3f,Damping=.92f,Gravity=9.81f,LinearInertia=.08f,AirDragMultiplier=.04f,Wind=.015f,MaxLinearVelocity=4,LinearVelocityMultiplier=1};
foreach(var asset in pkg.Items)asset.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(asset,null);
pkg.Save(args[1]);Console.WriteLine("Mapped shared proxy: "+touched.Count+" render groups; "+args[1]);
