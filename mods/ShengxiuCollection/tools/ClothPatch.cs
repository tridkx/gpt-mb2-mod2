using TpacTool.Lib;
using System.Text.Json;
using System.Security.Cryptography;

// Own mod only: add generated constraints and fill missing editor skin records.
// Geometry/indices/vertex colors/runtime skin weights are never changed.
var pkg=new AssetPackage(args[0],true,false);
using var manifest=JsonDocument.Parse(File.ReadAllText(args[1]));
var type=new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e");
var changed=0;
foreach(var row in manifest.RootElement.EnumerateArray()) {
 var mm=pkg.Items.OfType<Metamesh>().Single(m=>m.Name==row.GetProperty("metamesh").GetString());
 if(!mm.Name.StartsWith("sx_mingyu_"))throw new Exception("Not a Mingyu mesh");
 var mesh=mm.Meshes.Single(m=>m.Guid==row.GetProperty("guid").GetGuid());
 if(!mesh.Flags.Contains("uses_cloth_simulation"))throw new Exception("Cloth flag missing");
 var raw=File.ReadAllBytes(row.GetProperty("path").GetString()!);
 if(Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant()!=row.GetProperty("sha256").GetString())
  throw new Exception("Cooked blob hash mismatch");
 var data=new ExternalData(type);
 using(var reader=new BinaryReader(new MemoryStream(raw)))data.ReadData(reader,new Dictionary<object,object>(),raw.Length);
 mm.TypelessDataSegments.RemoveAll(s=>s.TypeGuid==type&&s.OwnerGuid==mesh.Guid);
 mm.TypelessDataSegments.Add(new ExternalLoader<ExternalData>(data){OwnerGuid=mesh.Guid,UnknownUint=1});
 var ed=mesh.EditData.Data;var v=mesh.VertexStream.Data;
 var bones=new MeshEditData.Bone[ed.Positions.Length];
 var seen=new bool[bones.Length];
 for(int i=0;i<ed.Vertices.Length;i++) {
  var index=ed.Vertices[i].PositionIndex;
  if(seen[index])throw new Exception("Expected builder's one editor position per vertex");
  seen[index]=true;
  var w=v.BoneWeights[i];var b=v.BoneIndices[i];
  bones[index]=new MeshEditData.Bone{W0=w.W1/255f,W1=w.W2/255f,W2=w.W3/255f,W3=w.W4/255f,
                                   B0=b.B1,B1=b.B2,B2=b.B3,B3=b.B4};
 }
 if(seen.Any(x=>!x))throw new Exception("Unassigned editor position");
 ed.Bones=bones;
 mesh.EditData.MarkLongLive(); // Loader otherwise only keeps a weak reference.
 changed++;
}
if(changed!=4)throw new Exception("Expected exactly 4 existing Mingyu cloth meshes");
pkg.Save(args[2]);
Console.WriteLine("Stored own cooked cloth segments and editor bones: "+changed+" meshes");
