using TpacTool.Lib;
var pkg=new AssetPackage(args[0],true,false);
var body=pkg.Items.OfType<Metamesh>().Single(x=>x.Name=="bql_body");
var changed=0;
foreach(var mesh in body.Meshes.Where(x=>x.Name.StartsWith("bql_part_13"))) {
 if(mesh.Flags.Contains("uses_cloth_simulation"))throw new Exception("Sleeve simulation must stay disabled");
 var filename=System.Text.RegularExpressions.Regex.Replace(mesh.Name,@"\.b\d+$","")+".mgeo";
 using var r=new BinaryReader(File.OpenRead(Path.Combine(args[1],filename)));
 if(r.ReadInt32()!=0x4f45474d)throw new Exception("Bad geometry header");var n=r.ReadInt32();var ni=r.ReadInt32();var v=mesh.VertexStream.Data;
 if(n!=v.Positions.Length||ni!=v.Indices.Length)throw new Exception("Geometry order changed");
 for(int i=0;i<n;i++) {var p=v.Positions[i];if(Math.Abs(r.ReadSingle()-p.X)>0.000002||Math.Abs(r.ReadSingle()-p.Y)>0.000002||Math.Abs(r.ReadSingle()-p.Z)>0.000002)throw new Exception("Source geometry changed");}
 r.BaseStream.Position=12+n*60;var indices=r.ReadBytes(n*4);var weights=r.ReadBytes(n*4);
 for(int i=0;i<ni;i++)if(r.ReadUInt32()!=v.Indices[i])throw new Exception("Triangle order changed");
 for(int i=0;i<n;i++) {
  var b=v.BoneIndices[i];b.B1=indices[i*4];b.B2=indices[i*4+1];b.B3=indices[i*4+2];b.B4=indices[i*4+3];v.BoneIndices[i]=b;
  var w=v.BoneWeights[i];w.W1=weights[i*4];w.W2=weights[i*4+1];w.W3=weights[i*4+2];w.W4=weights[i*4+3];v.BoneWeights[i]=w;
 }
 mesh.VertexStream.MarkLongLive();var ed=mesh.EditData.Data;var bones=new MeshEditData.Bone[ed.Positions.Length];
 for(int i=0;i<n;i++){var b=v.BoneIndices[i];var w=v.BoneWeights[i];bones[ed.Vertices[i].PositionIndex]=new MeshEditData.Bone{B0=b.B1,B1=b.B2,B2=b.B3,B3=b.B4,W0=w.W1/255f,W1=w.W2/255f,W2=w.W3/255f,W3=w.W4/255f};}
 ed.Bones=bones;mesh.EditData.MarkLongLive();changed++;
}
if(changed!=4)throw new Exception("Expected four sleeve LODs");pkg.Save(args[2]);Console.WriteLine("Patched only sleeve skin weights across four LODs");
