using TpacTool.Lib;
var pkg=new AssetPackage(args[0],true,false);var donor=new AssetPackage(args[1],true,false);
var count=0;
foreach(var mm in pkg.Items.OfType<Metamesh>()) {
 bool changed=false;var newer=donor.Items.OfType<Metamesh>().Single(m=>m.Name==mm.Name);
 foreach(var mesh in mm.Meshes.Where(m=>mm.Name=="sx_mingyu_head"||m.Name.Split(".lod")[0]=="sx_mingyu_body_02")) {
  var n=newer.Meshes.Single(m=>m.Name==mesh.Name);
  int vi=mm.TypelessDataSegments.IndexOf(mesh.VertexStream),ei=mm.TypelessDataSegments.IndexOf(mesh.EditData);
  if(vi<0||ei<0)throw new Exception("Missing original streams");
  mesh.VertexStream=n.VertexStream;mesh.VertexStream.OwnerGuid=mesh.Guid;mesh.VertexStream.MarkLongLive();
  mesh.EditData=n.EditData;mesh.EditData.OwnerGuid=mesh.Guid;mesh.EditData.MarkLongLive();
  mm.TypelessDataSegments[vi]=mesh.VertexStream;mm.TypelessDataSegments[ei]=mesh.EditData;
  mesh.PositionCount=n.PositionCount;mesh.FaceCount=n.FaceCount;mesh.VertexCount=n.VertexCount;
  mesh.SkinDataSize=n.SkinDataSize;mesh.UnknownInt2=n.UnknownInt2;mesh.BoundingBox=n.BoundingBox;
  changed=true;count++;
 }
 if(changed)mm.GetType().BaseType!.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(mm,null);
}
if(count!=28)throw new Exception("Expected head and neck skin in all four LODs");
pkg.Save(args[2]);Console.WriteLine("Updated head and neck skin; accepted garments unchanged");
