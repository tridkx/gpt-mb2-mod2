using TpacTool.Lib;
using System.Text.Json;
using System.Reflection;
using System.Security.Cryptography;

var options = new JsonSerializerOptions { WriteIndented = true };
if (args[0] == "probe") {
    var shaders = new AssetPackage(args[2], true, false);
    var simple = shaders.Items.OfType<Shader>().Single(s => s.Name == "simple_shader");
    var pkg = new AssetPackage(args[1], true, false);
    var rows = pkg.Items.OfType<Material>().Where(m => m.Shader.Guid == simple.Guid || m.Name == "custom_banner_icons_01")
        .Select(m => new { m.Name, m.Guid, shader = m.Shader.Guid, m.BlendMode, m.Flags,
            m.VertexLayoutFlags, m.ShaderMaterialFlags, m.AlphaTest,
            textures = m.Textures.ToDictionary(p => p.Key.ToString(), p => p.Value.Guid.ToString()) });
    Console.WriteLine(JsonSerializer.Serialize(new { shader = simple.Guid, materials = rows }, options));
} else if (args[0] == "patch") {
    var pkg = new AssetPackage(args[1], true, true);
    var shaders = new AssetPackage(args[2], true, false);
    var simple = shaders.Items.OfType<Shader>().Single(s => s.Name == "simple_shader");
    var mat = pkg.Items.OfType<Material>().Single(m => m.Name == "bb_portrait_icons");
    mat.Shader = new AssetDependence<Shader>(simple.Guid);
    mat.ShaderMaterialFlags.Clear(); // Alpha blending retains hair edges and the approved soft halo.
    mat.BlendMode = "modulate";
    mat.AlphaTest = 0;
    foreach (var a in pkg.Items) {
        typeof(AssetItem).GetField("_rawMetadata", BindingFlags.Instance | BindingFlags.NonPublic)?.SetValue(a, null);
    }
    pkg.Save(args[3]);
    Console.WriteLine("Saved portrait banner assets: " + args[3]);
} else if (args[0] == "inspect") {
    var pkg = new AssetPackage(args[1], true, true);
    var textures = pkg.Items.OfType<Texture>().Select(t => new {
        t.Name, t.Guid, width = t.Width, height = t.Height, mips = t.MipmapCount,
        format = t.Format.ToString(), flags = t.Flags, systemFlags = t.SystemFlags,
        arrays = t.ArrayCount,
        pixel_sha256 = Convert.ToHexString(SHA256.HashData(t.TexturePixels.Data.RawImage[0][0]))
    });
    var materials = pkg.Items.OfType<Material>().Select(m => new {
        m.Name, m.Guid, shader = m.Shader.Guid, m.BlendMode, m.AlphaTest, m.Flags,
        m.VertexLayoutFlags, m.ShaderMaterialFlags,
        textures = m.Textures.ToDictionary(p => p.Key.ToString(), p => p.Value.Guid.ToString())
    });
    Console.WriteLine(JsonSerializer.Serialize(new { package_guid = pkg.Guid, textures, materials,
        assets = pkg.Items.Select(a => new { a.Name, a.Guid, type = a.GetType().Name }) }, options));
} else { throw new ArgumentException("Use probe, patch or inspect"); }
