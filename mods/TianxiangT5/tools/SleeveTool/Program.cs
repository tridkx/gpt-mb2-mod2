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
            multiplier=m.UnknownFloat1, cloth=m.ClothingMaterial,
            pos=v.Positions.Select(p => new[]{p.X,p.Y,p.Z}),
            normal=v.Normals.Select(p => new[]{p.X,p.Y,p.Z}),
            uv=v.Uv1.Select(p => new[]{p.X,p.Y}), idx=v.Indices,
            color=v.Colors1.Select(c => new[]{(int)c.R,c.G,c.B,c.A}),
            bi=v.BoneIndices.Select(b => new[]{(int)b.B1,b.B2,b.B3,b.B4}),
            bw=v.BoneWeights.Select(b => new[]{(int)b.W1,b.W2,b.W3,b.W4}) };
    }));
    File.WriteAllText(args[2], JsonSerializer.Serialize(meshes));
    Console.WriteLine("Dumped final mesh data: " + args[2]);
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
