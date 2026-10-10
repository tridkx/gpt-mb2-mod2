using TpacTool.Lib;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Numerics;
var package=new AssetPackage(args[0],true,false);
using var handMorphs=JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(args[2])!,"hand_morphs.json")));
using var geometry=JsonDocument.Parse(File.ReadAllText(args[2]));
var rows=geometry.RootElement.EnumerateArray().ToDictionary(x=>x.GetProperty("name").GetString()!);
foreach(var mesh in package.Items.OfType<Metamesh>()) {
    if(!mesh.Name.StartsWith("wdr_"))throw new InvalidDataException("Unexpected mesh namespace");
    mesh.UnknownString=mesh.Name=="wdr_canglan_body"?"wdr_canglan_collision":"";
    foreach(var group in mesh.Meshes) {
        var match=Regex.Match(group.Name,@"\.lod(\d+)");
        group.Lod=match.Success?int.Parse(match.Groups[1].Value):0;
        bool cloth=rows[group.Name].GetProperty("cloth").GetBoolean();
        group.Flags=cloth?new List<string>{"uses_cloth_simulation","force_enable_cloth"}:new List<string>();
        if(mesh.Name=="wdr_canglan_hands") {
            var frames=handMorphs.RootElement.GetProperty(group.Name);var ed=group.EditData.Data;
            ed.MorphFrames.Clear();
            foreach(var f in frames.EnumerateArray()) {
                Vector4[] ReadVectors(string key,bool position)=>f.GetProperty(key).EnumerateArray().Select(v=>new Vector4(v[0].GetSingle(),v[1].GetSingle(),v[2].GetSingle(),1)).ToArray();
                ed.MorphFrames.Add(new MeshEditData.VertexFrame{Time=f.GetProperty("time").GetInt32(),Positions=ReadVectors("positions",true),Normals=ReadVectors("normals",false)});
            }
            group.VertexKeyCount=ed.MorphFrames.Count;
            group.EditData.MarkLongLive();
        }
        if(cloth) {
            group.UnknownFloat1=1;group.UnknownInt3=120;group.UnknownBool1=true;group.UnknownBool2=false;group.UnknownBool3=true;
            group.ClothingMaterial=new ClothingMaterial{Name="wdr_canglan_fabric",BendingStiffness=.22f,ShearingStiffness=.9f,StretchingStiffness=1,AnchorStiffness=1,Damping=.65f,Gravity=9.81f,LinearInertia=.12f,AirDragMultiplier=.08f,Wind=.025f,MaxLinearVelocity=4,LinearVelocityMultiplier=.5f};
        }
    }
}
foreach(var asset in package.Items)asset.GetType().BaseType?.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(asset,null);
package.Save(args[1]);
