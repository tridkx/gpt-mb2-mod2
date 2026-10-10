using System.Numerics;
using System.Text.Json;
using TpacTool.Lib;
float[] V3(Vector3 v)=>new[]{v.X,v.Y,v.Z};
float[] V4(Vector4 v)=>new[]{v.X,v.Y,v.Z,v.W};
var pkg=new AssetPackage(args[0],true,false);
var mm=pkg.Items.OfType<Metamesh>().Single(m=>m.Name==args[1]);
var result=mm.Meshes.Select(m=>{
 var s=m.VertexStream?.Data;var e=m.EditData?.Data;
 return new {m.Name,m.Lod,m.VertexKeyCount,m.VertexCount,m.PositionCount,m.SkinDataSize,m.Flags,m.MaterialFlags,material=m.Material.Guid,
 positions=s?.Positions.Select(V3),another_positions=s?.UnknownAnotherPositions.Select(V3),normals=s?.Normals.Select(V3),indices=s?.Indices,
 bones=s?.BoneIndices.Select(b=>new[]{(int)b.B1,b.B2,b.B3,b.B4}),weights=s?.BoneWeights.Select(b=>new[]{(int)b.W1,b.W2,b.W3,b.W4}),
 compressed_positions=s?.CompressedPositions.Select(p=>new[]{(float)p.X,(float)p.Y,(float)p.Z,(float)p.W}),compressed_normals_count=s?.CompressedNormals.Length,compressed_tangents_count=s?.CompressedTangents.Length,qtangent_count=s?.TangentTransform?.Length,
 edit_positions=e?.Positions.Select(V4),edit_vertex_position_indices=e?.Vertices.Select(v=>v.PositionIndex),
 frames=e?.MorphFrames.Select(f=>new {f.Time,positions=f.Positions.Select(V4),normals=f.Normals.Select(V4)})};
});
File.WriteAllText(args[2],JsonSerializer.Serialize(result));
Console.WriteLine("HAND_PROBE "+mm.Name+" meshes="+mm.Meshes.Count);
