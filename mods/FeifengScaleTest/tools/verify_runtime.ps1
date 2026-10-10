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
  $taskActual=$taskMethod.Invoke($null,@([single]$taskCase[0]))
  if($taskActual -ne $taskCase[1]){throw "Phase boundary failed at $($taskCase[0])"}
 }
 $taskHead=$taskType.GetField('Head',[Reflection.BindingFlags]'Static,NonPublic').GetValue($null)
 $taskScale=$taskType.GetField('DoubleHead',[Reflection.BindingFlags]'Static,NonPublic').GetValue($null)
 if($taskHead.Length -ne 1 -or $taskHead[0] -ne 13){throw 'Not a sparse head-only call'}
 if($taskScale.Length -ne 1){throw 'Incorrect diagnostic scale count'}
 Add-Type -TypeDefinition @"
public static class HeadScaleCheck {
 public static void Verify(object value) {
  object v=((System.Array)value).GetValue(0);
  foreach(string axis in new[]{"x","y","z"})
   if((float)v.GetType().GetField(axis).GetValue(v)!=2f)
    throw new System.Exception("Incorrect diagnostic multiplier");
 }
}
"@
 [HeadScaleCheck]::Verify($taskScale)
 $taskAll=$taskType.GetField('All',[Reflection.BindingFlags]'Static,NonPublic').GetValue($null)
 if($taskAll.Length -ne 28){throw 'Incomplete restore indices'}
 for($taskI=0;$taskI -lt 28;$taskI++){if($taskAll[$taskI] -ne $taskI){throw 'Incorrect restore index'}}
 Write-Output 'COMPILED_DIAGNOSTIC_CHECKS_PASS: 10 phase boundaries; sparse head 13 x2; restore 0..27'
} finally {[AppDomain]::CurrentDomain.remove_AssemblyResolve($taskResolver)}
