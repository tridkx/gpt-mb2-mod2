using TpacTool.Lib;
var pkg=new AssetPackage(args[0],true,false);
if(args[1]=="--verify") {
 foreach(var mm in pkg.Items.OfType<Metamesh>()) {
 if(mm.UnknownString!=""||mm.Meshes.Any(m=>m.Flags.Any(f=>f.Contains("cloth"))))throw new Exception("Cloth enabled");
 if(mm.TypelessDataSegments.Any(s=>s.TypeGuid==new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e")))throw new Exception("Cooked cloth remains");
 }
 Console.WriteLine("Final package: zero cloth flags, payloads and body references");return;
}
if(Path.GetFullPath(args[0])==Path.GetFullPath(args[1]))throw new Exception("Preserve input");
var cloth=new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e");var map=new Guid("af41613e-bd4f-4f8f-9fbf-7254858d9ff6");
int groups=0,segments=0;
foreach(var mm in pkg.Items.OfType<Metamesh>()) {
 if(!mm.Name.StartsWith(args[2]+"_"))throw new Exception("Unexpected asset scope");
 mm.UnknownString="";
 int old=mm.TypelessDataSegments.Count;
 // The baseline uses direct simulation; remove all direct-cloth payloads.
 mm.TypelessDataSegments.RemoveAll(s=>s.TypeGuid==cloth||s.TypeGuid==map);segments+=old-mm.TypelessDataSegments.Count;
 foreach(var mesh in mm.Meshes) {
 mesh.Flags.RemoveAll(f=>f=="uses_cloth_simulation"||f=="force_enable_cloth");
 mesh.UnknownFloat1=0;mesh.UnknownInt3=0;mesh.UnknownBool1=false;mesh.UnknownBool2=false;mesh.UnknownBool3=false;
 mesh.ClothingMaterial=new ClothingMaterial();groups++;
 }
}
foreach(var asset in pkg.Items)asset.GetType().BaseType.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)?.SetValue(asset,null);
pkg.Save(args[1]);Console.WriteLine($"Disabled cloth: {groups} groups; removed {segments} cooked segments");
