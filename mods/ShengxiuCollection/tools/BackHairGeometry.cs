using TpacTool.Lib;
// Hair-only transplant from the v1.1.6 package; retain accepted head/neck/body.
var pkg=new AssetPackage(args[0],true,false);
var donor=new AssetPackage(args[1],true,false);
var head=pkg.Items.OfType<Metamesh>().Single(m=>m.Name=="sx_mingyu_head");
var newer=donor.Items.OfType<Metamesh>().Single(m=>m.Name==head.Name);
var count=0;
foreach(var mesh in head.Meshes.Where(m=>m.Name=="sx_mingyu_head_00"||m.Name.StartsWith("sx_mingyu_head_00.lod"))) {
 var n=newer.Meshes.Single(m=>m.Name==mesh.Name);
 var vi=head.TypelessDataSegments.IndexOf(mesh.VertexStream);var ei=head.TypelessDataSegments.IndexOf(mesh.EditData);
 if(vi<0||ei<0)throw new Exception("Original geometry segments missing");
 mesh.VertexStream=n.VertexStream;mesh.VertexStream.OwnerGuid=mesh.Guid;mesh.VertexStream.MarkLongLive();
 mesh.EditData=n.EditData;mesh.EditData.OwnerGuid=mesh.Guid;mesh.EditData.MarkLongLive();
 head.TypelessDataSegments[vi]=mesh.VertexStream;head.TypelessDataSegments[ei]=mesh.EditData;
 mesh.PositionCount=n.PositionCount;mesh.FaceCount=n.FaceCount;mesh.VertexCount=n.VertexCount;
 mesh.SkinDataSize=n.SkinDataSize;mesh.UnknownInt2=n.UnknownInt2;mesh.BoundingBox=n.BoundingBox;
 if(mesh.Lod==0) {
  mesh.ClothingMaterial.Name="sx_mingyu_free_hair";
  mesh.ClothingMaterial.BendingStiffness=0.18f;
 }
 count++;
}
if(count!=4)throw new Exception("Expected four hair LODs");
head.GetType().BaseType!.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(head,null);
pkg.Save(args[2]);Console.WriteLine("Four hair streams replaced; long-hair bending 0.18; other resources preserved");
