using TpacTool.Lib;
// Single-variable game test: keep cloth solver, materials, geometry and blobs.
if(args.Length!=2 || Path.GetFullPath(args[0])==Path.GetFullPath(args[1]))
    throw new Exception("Provide distinct baseline and candidate paths");
var pkg=new AssetPackage(args[0],true,false);
var changed=0;
foreach(var mm in pkg.Items.OfType<Metamesh>()) {
    if(mm.Name is not ("sx_mingyu_head" or "sx_mingyu_body"))continue;
    if(mm.UnknownString!="human_body")throw new Exception("Unexpected collision baseline");
    mm.UnknownString="";
    var field=mm.GetType().BaseType!.GetField("_rawMetadata",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
    field?.SetValue(mm,null);changed++;
}
if(changed!=2)throw new Exception("Expected Mingyu head and body only");
pkg.Save(args[1]);
Console.WriteLine("Mingyu collision isolation: 2 references cleared; cloth retained");
