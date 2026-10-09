using TpacTool.Lib;
using System.Text.RegularExpressions;
var package=new AssetPackage(args[0],true,false);
foreach(var mesh in package.Items.OfType<Metamesh>()) {
 if(!mesh.Name.StartsWith("ffs_"))throw new InvalidDataException("Unexpected mesh namespace");
 mesh.UnknownString="human_body";
 foreach(var group in mesh.Meshes) {
  var match=Regex.Match(group.Name,@"\.lod(\d+)");group.Lod=match.Success?int.Parse(match.Groups[1].Value):0;group.Flags=new List<string>();
 }
}
foreach(var asset in package.Items)asset.GetType().BaseType?.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(asset,null);
package.Save(args[1]);
