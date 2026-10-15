using TpacTool.Lib;
using System.Runtime.InteropServices;
using System.Text.Json;
if(args[0]=="check-bc-texture") {
 int hr=Gpu.D3D11CreateDevice(IntPtr.Zero,5,IntPtr.Zero,0,IntPtr.Zero,0,7,out var device,out var level,out var context);
 Marshal.ThrowExceptionForHR(hr);
 var create=Marshal.GetDelegateForFunctionPointer<Gpu.CreateTexture2D>(Marshal.ReadIntPtr(Marshal.ReadIntPtr(device),5*IntPtr.Size));
 var rows=new List<object>();
 foreach(var width in new uint[]{1181,2048}) {
  var desc=new Gpu.TextureDesc{Width=width,Height=width,MipLevels=1,ArraySize=1,Format=77,SampleCount=1,BindFlags=8};
  int result=create(device,ref desc,IntPtr.Zero,out var texture);if(texture!=IntPtr.Zero)Marshal.Release(texture);
  rows.Add(new{width,height=width,format="BC3_UNORM",hresult=$"0x{result:X8}",success=result>=0});
 }
 Marshal.Release(context);Marshal.Release(device);Console.WriteLine(JsonSerializer.Serialize(rows));return;
}
var package=new AssetPackage(args[1],true,false);
if(args[0]=="native-driver") {
 var proxy=package.Items.OfType<Metamesh>().Single(m=>m.Name==args[3]+"_cloth_proxy");
 proxy.UnknownString="";
 foreach(var mesh in proxy.Meshes) {mesh.Flags=new List<string>();mesh.UnknownBool1=false;mesh.UnknownBool2=false;mesh.UnknownBool3=false;}
 var body=package.Items.OfType<Metamesh>().Single(m=>m.ClothMetamesh==proxy.Guid);
 foreach(var mesh in body.Meshes.Where(m=>m.Flags.Contains("uses_cloth_simulation"))) {
  mesh.Flags.Remove("force_enable_cloth");mesh.UnknownBool1=false;mesh.UnknownBool2=false;mesh.UnknownBool3=false;
 }
} else if(args[0]=="replace-texture") {
 var donor=new AssetPackage(args[3],true,false);var original=package.Items.OfType<Texture>().Single(t=>t.Name==args[4]);var replacement=donor.Items.OfType<Texture>().Single();
 var donorGuid=replacement.Guid;replacement.Guid=original.Guid;replacement.Name=original.Name;
 foreach(var segment in replacement.TypelessDataSegments)if(segment.OwnerGuid==donorGuid)segment.OwnerGuid=original.Guid;
 package.Items[package.Items.IndexOf(original)]=replacement;
} else throw new Exception("Unknown operation");
package.Save(args[2]);
static class Gpu {
 [DllImport("d3d11.dll")]public static extern int D3D11CreateDevice(IntPtr adapter,uint driverType,IntPtr software,uint flags,IntPtr levels,uint numLevels,uint sdk,out IntPtr device,out uint featureLevel,out IntPtr context);
 [StructLayout(LayoutKind.Sequential)]public struct TextureDesc {public uint Width,Height,MipLevels,ArraySize,Format,SampleCount,SampleQuality,Usage,BindFlags,CPUAccessFlags,MiscFlags;}
 [UnmanagedFunctionPointer(CallingConvention.StdCall)]public delegate int CreateTexture2D(IntPtr device,ref TextureDesc desc,IntPtr initialData,out IntPtr texture);
}
