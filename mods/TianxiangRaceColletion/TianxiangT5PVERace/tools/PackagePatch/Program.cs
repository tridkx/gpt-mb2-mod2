using TpacTool.Lib;
using System.Text.RegularExpressions;
var p=new AssetPackage(args[0],true,false);
foreach(var mesh in p.Items.OfType<Metamesh>()) {
 if(!mesh.Name.StartsWith("txt5pve_")) throw new InvalidDataException("Unexpected namespace");
 mesh.UnknownString="";
 foreach(var g in mesh.Meshes) {var m=Regex.Match(g.Name,@"\.lod(\d+)");g.Lod=m.Success?int.Parse(m.Groups[1].Value):0;g.Flags=new List<string>();}
}
foreach(var a in p.Items) a.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(a,null);
p.Save(args[1]);
