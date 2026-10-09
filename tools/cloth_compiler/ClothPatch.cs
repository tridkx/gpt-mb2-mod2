using TpacTool.Lib;
using System.Text.Json;
using System.Security.Cryptography;

// Explicitly selected metameshes only: add generated constraints and editor skin.
// Geometry/indices/vertex colors/runtime skin weights are never changed.
var pkg=new AssetPackage(args[0],true,false);
if(args.Length<5||args[3]!="--allow-metameshes")throw new Exception("Supply --allow-metameshes with the target mod's exact metamesh names");
if(string.Equals(Path.GetFullPath(args[0]),Path.GetFullPath(args[2]),StringComparison.OrdinalIgnoreCase))throw new Exception("Use a distinct output path; input package is preserved");
var allowed=args.Skip(4).ToHashSet();
using var manifest=JsonDocument.Parse(File.ReadAllText(args[1]));
var type=new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e");
var changed=0;
foreach(var row in manifest.RootElement.EnumerateArray()) {
 var mm=pkg.Items.OfType<Metamesh>().Single(m=>m.Name==row.GetProperty("metamesh").GetString());
 if(!allowed.Contains(mm.Name))throw new Exception("Metamesh outside explicit scope: "+mm.Name);
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
 if(v.BoneWeights.Length==0&&v.BoneIndices.Length==0) {changed++;continue;}
 if(v.BoneWeights.Length!=ed.Vertices.Length||v.BoneIndices.Length!=ed.Vertices.Length)throw new Exception("Editor/runtime vertex order must match; adapter required");
 var bones=new MeshEditData.Bone[ed.Positions.Length];
 var seen=new bool[bones.Length];
 for(int i=0;i<ed.Vertices.Length;i++) {
  var index=ed.Vertices[i].PositionIndex;
  var w=v.BoneWeights[i];var b=v.BoneIndices[i];
  var candidate=new MeshEditData.Bone{W0=w.W1/255f,W1=w.W2/255f,W2=w.W3/255f,W3=w.W4/255f,
                                   B0=b.B1,B1=b.B2,B2=b.B3,B3=b.B4};
  if(seen[index]&&!bones[index].Equals(candidate))throw new Exception("Shared editor position has conflicting skin weights");
  seen[index]=true;bones[index]=candidate;
 }
 if(seen.Any(x=>!x))throw new Exception("Unassigned editor position");
 ed.Bones=bones;
 mesh.EditData.MarkLongLive(); // Loader otherwise only keeps a weak reference.
 changed++;
}
if(changed==0)throw new Exception("Manifest contains no cloth meshes");
pkg.Save(args[2]);
Console.WriteLine("Stored own cooked cloth segments and editor bones: "+changed+" meshes");
