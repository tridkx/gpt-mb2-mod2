using TpacTool.Lib;
using System.Text.Json;
using System.Reflection;

if (args.Length < 3) throw new ArgumentException("dump <tpac> <json> | patch <baseline.tpac> <recipe.json> <out.tpac>");
var pkg = new AssetPackage(args[1], true, false);
if (args[0] == "dump") {
    var meshes = pkg.Items.OfType<Metamesh>().SelectMany(mm => mm.Meshes.Select(m => {
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
