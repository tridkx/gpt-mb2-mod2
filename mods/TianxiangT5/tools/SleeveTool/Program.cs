using TpacTool.Lib;
using System.Text.Json;
using System.Reflection;
using System.Numerics;

if (args.Length < 3) throw new ArgumentException("dump <tpac> <json> | patch <baseline.tpac> <recipe.json> <out.tpac>");
if(args[0]=="scanflags") {
    var found=new List<object>();var skipped=new List<string>();
    foreach(var path in Directory.EnumerateFiles(args[1],"*.tpac")){
        AssetPackage sample;try{sample=new AssetPackage(path,true,false);}catch{skipped.Add(Path.GetFileName(path));continue;}
        foreach(var asset in sample.Items.OfType<Metamesh>())foreach(var mesh in asset.Meshes)
            if(mesh.Flags.Contains("force_enable_cloth"))found.Add(new{file=Path.GetFileName(path),asset=asset.Name,mesh=mesh.Name,mesh.Lod,mesh.Flags});
    }
    File.WriteAllText(args[2],JsonSerializer.Serialize(new{found,skipped},new JsonSerializerOptions{WriteIndented=true}));
    Console.WriteLine("Native force-cloth examples: "+found.Count);return;
}
var pkg = new AssetPackage(args[1], true, false);
if (args[0] == "inspect") {
    var mm=pkg.Items.OfType<Metamesh>().Single(m=>m.Name==args[2]);
    Directory.CreateDirectory(args[3]);
    var segments=new List<object>();
    int i=0;
    foreach(var loader in mm.TypelessDataSegments) {
        var data=(ExternalData)loader.GetType().GetProperty("Data")!.GetValue(loader)!;
        using var stream=new MemoryStream();
        using(var writer=new BinaryWriter(stream,System.Text.Encoding.UTF8,true)) data.WriteData(writer,loader.UserData);
        var bytes=stream.ToArray(); var file=$"segment_{i++}_{loader.TypeGuid}.bin";
        File.WriteAllBytes(Path.Combine(args[3],file),bytes);
        segments.Add(new{file,owner=loader.OwnerGuid,type=loader.TypeGuid,bytes=bytes.Length,loader.UnknownUint,loader.UnknownUlong});
    }
    File.WriteAllText(Path.Combine(args[3],"metadata.json"),JsonSerializer.Serialize(new{
        mm.Name,mm.Guid,mm.ClothMetamesh,mm.MetaVersion,mm.Version,mm.UnknownString,mm.ClothUint,mm.ClothString,segments,
        meshes=mm.Meshes.Select(m=>new{m.Name,m.Guid,m.Lod,m.Flags,m.UnknownFloat1,m.UnknownInt3,m.UnknownBool1,m.UnknownBool2,m.UnknownBool3,m.ClothingMaterial,m.VertexCount,m.PositionCount,m.SkinDataSize,m.FaceCount,EditPositionCount=m.EditData.Data.Positions.Length,EditBoneCount=m.EditData.Data.Bones.Length})
    },new JsonSerializerOptions{WriteIndented=true}));
    Console.WriteLine("Inspected "+mm.Name+": "+segments.Count+" segments");
} else if (args[0] == "dump") {
    var meshes = pkg.Items.OfType<Metamesh>().Where(mm=>args.Length<4||mm.Name==args[3]).SelectMany(mm => mm.Meshes.Select(m => {
        var v = m.VertexStream.Data;
        return new { name=m.Name, lod=m.Lod, flags=m.Flags, body=mm.UnknownString,
            multiplier=m.UnknownFloat1, cloth=m.ClothingMaterial, material=m.Material.Guid,
            pos=v.Positions.Select(p => new[]{p.X,p.Y,p.Z}),
            normal=v.Normals.Select(p => new[]{p.X,p.Y,p.Z}),
            tangent=v.Tangents.Select(t => new[]{t.X,t.Y,t.Z,t.W}), uv=v.Uv1.Select(p => new[]{p.X,p.Y}), idx=v.Indices,
            color=v.Colors1.Select(c => new[]{(int)c.R,c.G,c.B,c.A}),
            bi=v.BoneIndices.Select(b => new[]{(int)b.B1,b.B2,b.B3,b.B4}),
            bw=v.BoneWeights.Select(b => new[]{(int)b.W1,b.W2,b.W3,b.W4}) };
    }));
    File.WriteAllText(args[2], JsonSerializer.Serialize(meshes));
    Console.WriteLine("Dumped final mesh data: " + args[2]);
} else if (args[0] == "appearance") {
    using var doc=JsonDocument.Parse(File.ReadAllText(args[2]));
    var settings=doc.RootElement.GetProperty("meshes");
    var skin=pkg.Items.OfType<Material>().Single(m=>m.Name=="tx5_skin");
    foreach(var mm in pkg.Items.OfType<Metamesh>()) {
        if(mm.ClothMetamesh!=Guid.Empty || mm.TypelessDataSegments.Any(s=>s.TypeGuid==Guid.Parse("b97e0f10-df49-4666-8f1d-ada6630d4b4e")||s.TypeGuid==Guid.Parse("af41613e-bd4d-46ec-8284-debb56c042dc")))throw new Exception("Expected v1.4.0 baseline without simulation segments");
        foreach(var m in mm.Meshes) {
            m.Flags=m.Flags.Where(f=>f!="uses_cloth_simulation"&&f!="force_enable_cloth").ToList();
            if(m.Name.StartsWith("tx5_legs_06"))m.Material=new AssetDependence<Material>(skin.Guid);
            if(!settings.TryGetProperty(m.Name,out var r))continue;
            var v=m.VertexStream.Data;var ed=m.EditData.Data;int count=v.Positions.Length;
            if(ed.Vertices.Length!=count || ed.Positions.Length!=count)throw new Exception("Unexpected edit layout");
            var ids=r.GetProperty("keep").EnumerateArray().Select(x=>x.GetInt32()).ToArray();
            var originals=ed.Vertices;
            foreach(var prop in typeof(VertexStreamData).GetProperties().Where(p=>p.CanWrite&&p.PropertyType.IsArray&&p.Name!="Indices")) {
                var old=(Array?)prop.GetValue(v);if(old==null||old.Length==0)continue;
                if(old.Length!=count)throw new Exception("Unexpected array "+prop.Name);
                var arr=Array.CreateInstance(prop.PropertyType.GetElementType()!,ids.Length);
                for(int i=0;i<ids.Length;i++)arr.SetValue(old.GetValue(ids[i]),i);
                prop.SetValue(v,arr);
            }
            v.Indices=r.GetProperty("idx").EnumerateArray().Select(x=>x.GetInt32()).ToArray();
            if(r.TryGetProperty("pos",out var ps)) {
                v.Positions=ps.EnumerateArray().Select(x=>new Vector3(x[0].GetSingle(),x[1].GetSingle(),x[2].GetSingle())).ToArray();
                var ns=r.GetProperty("normal").EnumerateArray().ToArray();var ts=r.GetProperty("tangent").EnumerateArray().ToArray();
                for(int i=0;i<ids.Length;i++) {
                    var cp=v.CompressedPositions[i];cp.X=(SystemHalf.Half)v.Positions[i].X;cp.Y=(SystemHalf.Half)v.Positions[i].Y;cp.Z=(SystemHalf.Half)v.Positions[i].Z;v.CompressedPositions[i]=cp;
                    var n=new Vector3(ns[i][0].GetSingle(),ns[i][1].GetSingle(),ns[i][2].GetSingle());
                    var t=new Vector4(ts[i][0].GetSingle(),ts[i][1].GetSingle(),ts[i][2].GetSingle(),ts[i][3].GetSingle());
                    if(n==v.Normals[i]&&t==v.Tangents[i])continue;
                    v.Normals[i]=n;v.Tangents[i]=t;
                    var cn=new VertexStreamData.X11Y11Z10();cn.X=n.X;cn.Y=n.Y;cn.Z=n.Z;v.CompressedNormals[i]=cn;
                    var ct=new VertexStreamData.X10Y11Z10W1();ct.X=t.X;ct.Y=t.Y;ct.Z=t.Z;ct.Sign=t.W<0?-1:1;v.CompressedTangents[i]=ct;
                    var nn=Vector3.Normalize(n);var tv=Vector3.Normalize(new Vector3(t.X,t.Y,t.Z)-nn*Vector3.Dot(nn,new Vector3(t.X,t.Y,t.Z)));
                    v.TangentTransform[i]=Appearance.QuatFromColumns(tv,Vector3.Cross(nn,tv),nn);
                }
            }
            var oldPositions=ed.Positions;
            ed.Positions=ids.Select((id,i)=>new Vector4(v.Positions[i],oldPositions[originals[id].PositionIndex].W)).ToArray();
            ed.Vertices=ids.Select((id,i)=>{var x=originals[id];x.PositionIndex=(uint)i;
                if(r.TryGetProperty("pos",out _)){x.Normal=new Vector4(v.Normals[i],0);x.Padding=x.Normal;x.Tangent=new Vector4(v.Tangents[i].X,v.Tangents[i].Y,v.Tangents[i].Z,0);x.Binormal=new Vector4(Vector3.Cross(v.Normals[i],new Vector3(v.Tangents[i].X,v.Tangents[i].Y,v.Tangents[i].Z)),0);}
                return x;}).ToArray();
            if(ed.UnusedVec3.Length==count)ed.UnusedVec3=ids.Select(id=>ed.UnusedVec3[id]).ToArray();
#pragma warning disable CS0612
            if(ed.Bones.Length==count)ed.Bones=ids.Select(id=>ed.Bones[originals[id].PositionIndex]).ToArray();
#pragma warning restore CS0612
            ed.Faces=Enumerable.Range(0,v.Indices.Length/3).Select(i=>new MeshEditData.Face{V0=v.Indices[3*i],V1=v.Indices[3*i+1],V2=v.Indices[3*i+2]}).ToArray();
            m.VertexCount=m.PositionCount=m.SkinDataSize=ids.Length;m.FaceCount=ed.Faces.Length;
            m.BoundingBox=new BoundingBox(v.Positions.Aggregate(Vector3.Min),v.Positions.Aggregate(Vector3.Max));
            m.VertexStream.MarkLongLive();m.EditData.MarkLongLive();
        }
        mm.RawMetadata=null;
    }
    pkg.Save(args[3]);Console.WriteLine("Appearance repair saved; all cloth disabled");
} else if (args[0] == "windoff") {
    var proxy=pkg.Items.OfType<Metamesh>().Single(m=>m.Name=="tx5_cloth_simulation");
    if(proxy.Meshes.Count!=1)throw new Exception("Unexpected proxy layout");
    var mesh=proxy.Meshes.Single();var material=mesh.ClothingMaterial;
    if(Math.Abs(material.Wind-0.08f)>0.000001f)throw new Exception("Expected immutable v1.5.0 wind baseline");
    material.Wind=0;mesh.ClothingMaterial=material;proxy.RawMetadata=null;
    pkg.Save(args[2]);Console.WriteLine("Only proxy wind changed from 0.08 to 0; original simulation segments retained");
} else if (args[0] == "direct") {
    using var doc=JsonDocument.Parse(File.ReadAllText(args[2]));var recipe=doc.RootElement;
    var allowed=new HashSet<string>{"tx5_body_00","tx5_body_00.lod1","tx5_body_03","tx5_head_01"};
    if(pkg.Items.OfType<Metamesh>().Any(m=>m.ClothMetamesh!=Guid.Empty))throw new Exception("Direct baseline must have no proxy reference");
    foreach(var setting in recipe.GetProperty("meshes").EnumerateObject()) {
        if(!allowed.Contains(setting.Name))throw new Exception("Unexpected direct cloth target");
        var owner=pkg.Items.OfType<Metamesh>().Single(mm=>mm.Meshes.Any(m=>m.Name==setting.Name));
        var mesh=owner.Meshes.Single(m=>m.Name==setting.Name);var value=setting.Value;
        var alpha=value.GetProperty("alpha").EnumerateArray().Select(a=>a.GetByte()).ToArray();
        if(alpha.Length!=mesh.VertexStream.Data.Colors1.Length)throw new Exception("Alpha count mismatch");
        for(int i=0;i<alpha.Length;i++)mesh.VertexStream.Data.Colors1[i].A=alpha[i];
        var edit=mesh.EditData.Data;
        if(edit.Vertices.Length!=alpha.Length)throw new Exception("Edit/runtime vertex count mismatch");
        var reps=value.GetProperty("position_representatives").EnumerateArray().Select(x=>x.GetInt32()).ToArray();
        var positionIndex=value.GetProperty("vertex_to_position").EnumerateArray().Select(x=>x.GetUInt32()).ToArray();
        var stream=mesh.VertexStream.Data;
        edit.Positions=reps.Select(i=>new Vector4(stream.Positions[i],1)).ToArray();
        for(int i=0;i<alpha.Length;i++){edit.Vertices[i].Color.A=alpha[i];edit.Vertices[i].PositionIndex=positionIndex[i];}
#pragma warning disable CS0612
        edit.Bones=reps.Select(i=>{var bi=stream.BoneIndices[i];var bw=stream.BoneWeights[i];return new MeshEditData.Bone{B0=bi.B1,B1=bi.B2,B2=bi.B3,B3=bi.B4,W0=bw.W1/255f,W1=bw.W2/255f,W2=bw.W3/255f,W3=bw.W4/255f};}).ToArray();
#pragma warning restore CS0612
        mesh.PositionCount=reps.Length;mesh.SkinDataSize=reps.Length;
        mesh.EditData.MarkLongLive();
        mesh.VertexStream.MarkLongLive();
        mesh.Flags=new List<string>{"uses_cloth_simulation"};
        mesh.UnknownFloat1=value.GetProperty("multiplier").GetSingle();
        mesh.ClothingMaterial=JsonSerializer.Deserialize<ClothingMaterial>(value.GetProperty("material").GetRawText())!;
        if(owner.TypelessDataSegments.Any(s=>s.OwnerGuid==mesh.Guid && s.TypeGuid==Guid.Parse("b97e0f10-df49-4666-8f1d-ada6630d4b4e")))throw new Exception("Baseline contains cooked target already");
        owner.TypelessDataSegments.Add(new ExternalLoader<RawClothSegment>(new RawClothSegment(Guid.Parse("b97e0f10-df49-4666-8f1d-ada6630d4b4e"),File.ReadAllBytes(value.GetProperty("cooked").GetString()!))){OwnerGuid=mesh.Guid,UnknownUint=1});
        owner.RawMetadata=null;
    }
    pkg.Save(args[3]);Console.WriteLine("Wrote independently cooked direct cloth: "+args[3]);
} else if (args[0] == "mapped") {
    using var doc=JsonDocument.Parse(File.ReadAllText(args[2]));var recipe=doc.RootElement;
    var body=pkg.Items.OfType<Metamesh>().Single(m=>m.Name=="tx5_body");
    var originals=body.Meshes.ToDictionary(m=>m.Name);
    var sources=recipe.GetProperty("sources").EnumerateArray().Select(x=>(mesh:originals[x.GetProperty("mesh").GetString()!],index:x.GetProperty("index").GetInt32())).ToArray();
    var template=originals["tx5_body_00"];
    var proxyMesh=new Mesh();
    foreach(var prop in typeof(Mesh).GetProperties().Where(p=>p.CanRead&&p.CanWrite)) prop.SetValue(proxyMesh,prop.GetValue(template));
    proxyMesh.Name=recipe.GetProperty("name").GetString()!;
    proxyMesh.Guid=recipe.GetProperty("proxy_mesh_guid").GetGuid();
    proxyMesh.Lod=0;proxyMesh.Flags=recipe.GetProperty("flags").EnumerateArray().Select(x=>x.GetString()!).ToList();
    proxyMesh.VertexCount=sources.Length;proxyMesh.PositionCount=sources.Length;proxyMesh.SkinDataSize=sources.Length;
    proxyMesh.UnknownFloat1=recipe.GetProperty("multiplier").GetSingle();
    proxyMesh.ClothingMaterial=JsonSerializer.Deserialize<ClothingMaterial>(recipe.GetProperty("material").GetRawText())!;
    var v=new VertexStreamData();
    foreach(var prop in typeof(VertexStreamData).GetProperties().Where(p=>p.CanWrite&&p.PropertyType.IsArray&&p.Name!="Indices")) {
        var first=(Array?)prop.GetValue(sources[0].mesh.VertexStream.Data);
        if(first==null||first.Length==0){prop.SetValue(v,first);continue;}
        var array=Array.CreateInstance(prop.PropertyType.GetElementType()!,sources.Length);
        for(int i=0;i<sources.Length;i++) {
            var source=(Array)prop.GetValue(sources[i].mesh.VertexStream.Data)!;
            if(source.Length!=sources[i].mesh.VertexCount)throw new Exception("Vertex array length differs: "+prop.Name);
            array.SetValue(source.GetValue(sources[i].index),i);
        }
        prop.SetValue(v,array);
    }
    v.Indices=recipe.GetProperty("faces").EnumerateArray().Select(x=>x.GetInt32()).ToArray();
    var alpha=recipe.GetProperty("alpha").EnumerateArray().Select(x=>x.GetByte()).ToArray();
    for(int i=0;i<alpha.Length;i++)v.Colors1[i].A=alpha[i];
    proxyMesh.FaceCount=v.Indices.Length/3;
    proxyMesh.BoundingBox=new BoundingBox(v.Positions.Aggregate(Vector3.Min),v.Positions.Aggregate(Vector3.Max));
    proxyMesh.UnknownInt2=v.BoneIndices.SelectMany(b=>new[]{b.B1,b.B2,b.B3,b.B4}).Distinct().Count();
    proxyMesh.VertexStream=new ExternalLoader<VertexStreamData>(v){OwnerGuid=proxyMesh.Guid,UnknownUint=1};
    proxyMesh.VertexStream.UserData[VertexStreamData.KEY_HAS_QTANGENT]=true;
    var ed=new MeshEditData{Positions=v.Positions.Select(p=>new Vector4(p,1)).ToArray(),
        Vertices=new MeshEditData.Vertex[sources.Length],Faces=new MeshEditData.Face[proxyMesh.FaceCount]};
    for(int i=0;i<sources.Length;i++) {
        var item=sources[i].mesh.EditData.Data.Vertices[sources[i].index];
        item.PositionIndex=(uint)i;item.Color=v.Colors1[i];ed.Vertices[i]=item;
    }
    for(int i=0;i<ed.Faces.Length;i++)ed.Faces[i]=new(){V0=v.Indices[i*3],V1=v.Indices[i*3+1],V2=v.Indices[i*3+2]};
#pragma warning disable CS0612
    ed.Bones=sources.Select(s=>{
        var bi=s.mesh.VertexStream.Data.BoneIndices[s.index];var bw=s.mesh.VertexStream.Data.BoneWeights[s.index];
        return new MeshEditData.Bone{B0=bi.B1,B1=bi.B2,B2=bi.B3,B3=bi.B4,W0=bw.W1/255f,W1=bw.W2/255f,W2=bw.W3/255f,W3=bw.W4/255f};
    }).ToArray();
#pragma warning restore CS0612
    proxyMesh.EditData=new ExternalLoader<MeshEditData>(ed){OwnerGuid=proxyMesh.Guid};
    var proxy=new Metamesh{Name=proxyMesh.Name,Guid=recipe.GetProperty("proxy_guid").GetGuid(),
        MetaVersion=body.MetaVersion,Material=body.Material,UnknownFloat=body.UnknownFloat,
        UnknownBool1=body.UnknownBool1,UnknownBool2=body.UnknownBool2};
    proxy.Meshes.Add(proxyMesh);
    var cooked=new ExternalLoader<RawClothSegment>(new RawClothSegment(Guid.Parse("b97e0f10-df49-4666-8f1d-ada6630d4b4e"),File.ReadAllBytes(recipe.GetProperty("cooked").GetString()!))){OwnerGuid=proxyMesh.Guid,UnknownUint=1};
    proxy.ConsumeDataSegments(new AbstractExternalLoader[]{proxyMesh.EditData,proxyMesh.VertexStream,cooked});
    body.ClothMetamesh=proxy.Guid;body.RawMetadata=null;
    foreach(var name in recipe.GetProperty("disabled_render_meshes").EnumerateArray()) {
        if(name.GetString()!="tx5_body_03")throw new Exception("Unexpected cloth-disable target");
        originals[name.GetString()!].Flags=new List<string>();
    }
    foreach(var property in recipe.GetProperty("mapped").EnumerateObject()) {
        var mesh=originals[property.Name];
        if(property.Name.StartsWith("tx5_body_00")) {
            mesh.Flags=recipe.GetProperty("flags").EnumerateArray().Select(x=>x.GetString()!).ToList();
            var a=property.Value.GetProperty("alpha").EnumerateArray().Select(x=>x.GetByte()).ToArray();
            for(int i=0;i<a.Length;i++)mesh.VertexStream.Data.Colors1[i].A=a[i];
            mesh.VertexStream.MarkLongLive();
        }
        var mapping=new ExternalLoader<RawClothSegment>(new RawClothSegment(Guid.Parse("af41613e-bd4d-46ec-8284-debb56c042dc"),File.ReadAllBytes(property.Value.GetProperty("file").GetString()!))){OwnerGuid=mesh.Guid,UnknownUint=1};
        body.TypelessDataSegments.Add(mapping);
    }
    pkg.Items.Add(proxy);pkg.Save(args[3]);Console.WriteLine("Wrote proxy, cooked fabric and "+recipe.GetProperty("mapped").EnumerateObject().Count()+" mapped submeshes: "+args[3]);
} else if (args[0] == "patch") {
    using var doc = JsonDocument.Parse(File.ReadAllText(args[2]));
    var recipe = doc.RootElement;
    int changed = 0;
    foreach (var mm in pkg.Items.OfType<Metamesh>()) {
        bool modified = false;
        foreach (var m in mm.Meshes) {
            if (!recipe.GetProperty("meshes").TryGetProperty(m.Name, out var settings)) continue;
            if (mm.Name != "tx5_body" || m.Name != "tx5_body_00" && m.Name != "tx5_body_00.lod1")
                throw new Exception("Recipe attempts to modify a non-sleeve mesh");
            var alpha=settings.GetProperty("alpha").EnumerateArray().Select(a=>a.GetByte()).ToArray();
            var v=m.VertexStream.Data;
            if (alpha.Length != v.Positions.Length) throw new Exception("Vertex count differs");
            for (int i=0;i<alpha.Length;i++) v.Colors1[i].A=alpha[i];
            m.VertexStream.MarkLongLive();
            m.Flags = new List<string>{"uses_cloth_simulation"};
            m.UnknownFloat1 = settings.GetProperty("multiplier").GetSingle();
            m.ClothingMaterial = JsonSerializer.Deserialize<ClothingMaterial>(recipe.GetProperty("material").GetRawText())!;
            // Preserve collision body and version-specific boolean fields from the baseline.
            modified=true; changed++;
        }
        if (modified) {
            FieldInfo? field=null;
            for (Type? t=mm.GetType(); t!=null && field==null; t=t.BaseType)
                field=t.GetField("_rawMetadata", BindingFlags.Instance|BindingFlags.NonPublic);
            if (field!=null) field.SetValue(mm,null);
            else {
                var property=mm.GetType().GetProperty("RawMetadata");
                if (property==null) throw new Exception("Metadata cache interface not found");
                property.SetValue(mm,null);
            }
        }
    }
    if (changed != 2) throw new Exception("Expected exactly two sleeve LODs");
    pkg.Save(args[3]);
    Console.WriteLine("Patched sleeve LOD0/LOD1: " + args[3]);
} else throw new ArgumentException("Unknown command");

public sealed class RawClothSegment:ExternalData {
    public RawClothSegment():base(Guid.Parse("b97e0f10-df49-4666-8f1d-ada6630d4b4e")){}
    public RawClothSegment(Guid type,byte[] bytes):base(type){using var r=new BinaryReader(new MemoryStream(bytes));ReadData(r,new Dictionary<object,object>(),bytes.Length);}
}

public static class Appearance {
		public static VertexStreamData.SnormShort4 QuatFromColumns(Vector3 c0, Vector3 c1, Vector3 c2)
		{
			float m00 = c0.X, m10 = c0.Y, m20 = c0.Z;
			float m01 = c1.X, m11 = c1.Y, m21 = c1.Z;
			float m02 = c2.X, m12 = c2.Y, m22 = c2.Z;
			float tr = m00 + m11 + m22;
			float x, y, z, w;
			if (tr > 0)
			{
				float s = (float) Math.Sqrt(tr + 1.0) * 2f;
				w = 0.25f * s; x = (m21 - m12) / s; y = (m02 - m20) / s; z = (m10 - m01) / s;
			}
			else if (m00 > m11 && m00 > m22)
			{
				float s = (float) Math.Sqrt(1.0 + m00 - m11 - m22) * 2f;
				w = (m21 - m12) / s; x = 0.25f * s; y = (m01 + m10) / s; z = (m02 + m20) / s;
			}
			else if (m11 > m22)
			{
				float s = (float) Math.Sqrt(1.0 + m11 - m00 - m22) * 2f;
				w = (m02 - m20) / s; x = (m01 + m10) / s; y = 0.25f * s; z = (m12 + m21) / s;
			}
			else
			{
				float s = (float) Math.Sqrt(1.0 + m22 - m00 - m11) * 2f;
				w = (m10 - m01) / s; x = (m02 + m20) / s; y = (m12 + m21) / s; z = 0.25f * s;
			}
			if (w < 0) { x = -x; y = -y; z = -z; w = -w; }
			var q = new VertexStreamData.SnormShort4();
			q.X = x; q.Y = y; q.Z = z; q.W = w;
			return q;
		}

}
