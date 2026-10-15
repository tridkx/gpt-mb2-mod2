using Microsoft.Diagnostics.Runtime;
using System.Text.Json;
using var target=DataTarget.LoadDump(args[0]);
target.FileLocator=new LocalOnly();
var result=new List<object>();
foreach(var info in target.ClrVersions) {
 Console.Error.WriteLine($"CLR {info.Version}");
 using var runtime=info.CreateRuntime(@"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\mscordacwks.dll");
 Console.Error.WriteLine("Runtime ready");
 foreach(var thread in runtime.Threads) {
  if(!thread.IsAlive)continue;
  var frames=thread.EnumerateStackTrace().Take(64).Select(f=>new { ip=$"0x{f.InstructionPointer:x}",sp=$"0x{f.StackPointer:x}",kind=f.Kind.ToString(),name=f.Method?.Signature??f.ToString(),token=f.Method?.MetadataToken,module=f.Method?.Type?.Module?.Name}).ToArray();
  var ex=thread.CurrentException;
  var exceptions=new List<object>();
  for(var e=ex;e!=null;e=e.Inner)exceptions.Add(new {type=e.Type?.Name,message=e.Message,frames=e.StackTrace.Select(f=>new {name=f.Method?.Signature,token=f.Method?.MetadataToken,module=f.Method?.Type?.Module?.Name}).ToArray()});
  result.Add(new { thread=thread.OSThreadId, exception=ex?.Type?.Name,message=ex?.Message,exceptions,frames });
 }
}
Console.WriteLine(JsonSerializer.Serialize(result,new JsonSerializerOptions { WriteIndented=true }));

class LocalOnly:IFileLocator {
 string? Local(string name){
  if(File.Exists(name))return name;
  string root=@"D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord";
  var basename=Path.GetFileName(name);
  return Directory.EnumerateFiles(root,basename,SearchOption.AllDirectories).FirstOrDefault();
 }
 public string? FindPEImage(string name,int timestamp,int size,bool check)=>Local(name);
 public string? FindPEImage(string name,SymbolProperties props,System.Collections.Immutable.ImmutableArray<byte> id,System.Runtime.InteropServices.OSPlatform platform,bool check)=>Local(name);
 public string? FindElfImage(string name,SymbolProperties props,System.Collections.Immutable.ImmutableArray<byte> id,bool check)=>Local(name);
 public string? FindMachOImage(string name,SymbolProperties props,System.Collections.Immutable.ImmutableArray<byte> id,bool check)=>Local(name);
}
