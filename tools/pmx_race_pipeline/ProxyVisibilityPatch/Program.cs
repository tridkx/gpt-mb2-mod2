using TpacTool.Lib;
var package=new AssetPackage(args[0],true,false);
var donor=new AssetPackage(args[1],true,false);
var proxy=package.Items.OfType<Metamesh>().Single(m=>m.Name==args[3]+"_cloth_proxy");
var material=donor.Items.OfType<Material>().Single();
if(!material.ShaderMaterialFlags.Contains("alpha_test"))throw new Exception("Missing alpha test");
foreach(var item in donor.Items) {
 if(package.Items.Any(a=>a.Guid==item.Guid||a.Name==item.Name))throw new Exception("Duplicate donor asset");
 package.Items.Add(item);
}
proxy.Material=material.Guid;
foreach(var mesh in proxy.Meshes)mesh.Material=new AssetDependence<Material>(material.Guid);
proxy.GetType().BaseType?.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(proxy,null);
package.Save(args[2]);
Console.WriteLine("Proxy material changed; simulation geometry and payload retained");
