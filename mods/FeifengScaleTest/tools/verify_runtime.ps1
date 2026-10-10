param([string]$RuntimeDll)
$ErrorActionPreference='Stop'
$taskGameBin='D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/bin/Win64_Shipping_Client'
$taskResolver=[ResolveEventHandler]{param($sender,$event)
 $taskAssemblyName=([Reflection.AssemblyName]::new($event.Name)).Name
 $taskAssemblyPath=[IO.Path]::Combine($taskGameBin,($taskAssemblyName+'.dll'))
 if([IO.File]::Exists($taskAssemblyPath)){return [Reflection.Assembly]::LoadFrom($taskAssemblyPath)}
 return $null
}
[AppDomain]::CurrentDomain.add_AssemblyResolve($taskResolver)
try {
 $taskAssembly=[Reflection.Assembly]::LoadFrom((Resolve-Path -LiteralPath $RuntimeDll))
 $taskType=$taskAssembly.GetType('FeifengScaleTest.ScaleProbe',$true)
 $taskMethod=$taskType.GetMethod('PhaseAt',[Reflection.BindingFlags]'Static,NonPublic')
 $taskCases=@(@(0,0),@(5.99,0),@(6,1),@(17.99,1),@(18,2),@(23.99,2),@(24,3),@(35.99,3),@(36,4),@(1000,4))
 foreach($taskCase in $taskCases) {
  if($taskMethod.Invoke($null,@([single]$taskCase[0])) -ne $taskCase[1]){throw 'Phase boundary failed'}
 }
 Add-Type -ReferencedAssemblies @([IO.Path]::Combine($taskGameBin,'TaleWorlds.Library.dll'),[IO.Path]::Combine($taskGameBin,'System.Numerics.Vectors.dll'),'C:/Program Files (x86)/Reference Assemblies/Microsoft/Framework/.NETFramework/v4.7.2/Facades/netstandard.dll') -TypeDefinition @"
using System;
using System.Reflection;
using TaleWorlds.Library;
public static class LocalFrameCheck {
 static MatrixFrame Build(MethodInfo method,MatrixFrame parent,MatrixFrame current,MatrixFrame reference,float scale) {
  return (MatrixFrame)method.Invoke(null,new object[]{parent,current,reference,scale});
 }
 static void Near(float a,float b) {if(Math.Abs(a-b)>0.0001f)throw new Exception("Matrix check failed: "+a+" vs "+b);}
 static void Vector(Vec3 a,Vec3 b) {Near(a.x,b.x);Near(a.y,b.y);Near(a.z,b.z);}
 public static void Verify(Type type) {
  var method=type.GetMethod("BuildHeadLocal",BindingFlags.Static|BindingFlags.NonPublic);
  var parent=MatrixFrame.Identity;parent.rotation.s=new Vec3(.8f,.6f,0);parent.rotation.f=new Vec3(-.6f,.8f,0);parent.origin=new Vec3(.3f,-.4f,1.2f);
  var local=MatrixFrame.Identity;local.rotation.s=new Vec3(.6f,0,-.8f);local.rotation.u=new Vec3(.8f,0,.6f);local.origin=new Vec3(.07f,-.03f,.12f);
  var original=parent.TransformToParent(ref local);
  var reference=MatrixFrame.Identity;
  var scaled=Build(method,parent,original,reference,2f);
  Vector(scaled.origin,local.origin);
  Vector(parent.TransformToParent(ref scaled).origin,original.origin);
  Vector(scaled.rotation.s,local.rotation.s*2f);
  Vector(scaled.rotation.f,local.rotation.f*2f);
  Vector(scaled.rotation.u,local.rotation.u*2f);
  // Repeated writes must stay at x2 instead of growing exponentially.
  for(int i=0;i<1000;i++)scaled=Build(method,parent,parent.TransformToParent(ref scaled),reference,2f);
  Near(scaled.rotation.s.Length,2f);Near(scaled.rotation.f.Length,2f);Near(scaled.rotation.u.Length,2f);
  Vector(scaled.origin,local.origin);
  var restored=Build(method,parent,parent.TransformToParent(ref scaled),reference,1f);
  Vector(restored.origin,local.origin);
  Vector(restored.rotation.s,local.rotation.s);Vector(restored.rotation.f,local.rotation.f);Vector(restored.rotation.u,local.rotation.u);
 }
}
"@
 [LocalFrameCheck]::Verify($taskType)
 Write-Output 'COMPILED_LOCAL_FRAME_CHECKS_PASS: phase boundaries; rotated parent conversion; head origin unchanged; x2 axes; 1000 writes without accumulation; x1 restore'
} finally {[AppDomain]::CurrentDomain.remove_AssemblyResolve($taskResolver)}
