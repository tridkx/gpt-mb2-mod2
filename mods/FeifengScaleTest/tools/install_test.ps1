param([switch]$CheckOnly)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskSource=[IO.Path]::GetFullPath((Join-Path $taskRoot 'module/FeifengScaleTest'))
$taskModules=[IO.Path]::GetFullPath('D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules')
$taskTarget=[IO.Path]::GetFullPath((Join-Path $taskModules 'FeifengScaleTest'))
if (-not $taskTarget.StartsWith($taskModules+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside Modules' }
$taskReport=Get-Content -LiteralPath (Join-Path $taskRoot 'reports/release_validation.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($taskReport.status -ne 'pass' -or $taskReport.version -ne 'v0.1.0') { throw 'Missing structural validation for test version' }
if ((Get-FileHash -LiteralPath (Join-Path $taskSource 'AssetPackages/ffs.tpac') -Algorithm SHA256).Hash -ne $taskReport.final_package_sha256) { throw 'TPAC hash differs from report' }
if ((Get-FileHash -LiteralPath (Join-Path $taskSource 'bin/Win64_Shipping_Client/FeifengScaleTest.dll') -Algorithm SHA256).Hash -ne $taskReport.runtime_dll_sha256) { throw 'DLL hash differs from report' }
if ($CheckOnly) { Write-Output "Test inputs validated: $taskTarget"; return }
if (Get-Process | Where-Object {$_.ProcessName -match 'Bannerlord|TaleWorlds'}) { throw 'Exit game and launcher before installing' }
if (Test-Path -LiteralPath $taskTarget) { throw 'First-install script will not overwrite an existing module; preserve prior version first' }
foreach ($taskFile in Get-ChildItem -LiteralPath $taskSource -Recurse -File) {
 if ($taskFile.Name -eq '.gitkeep') { continue }
 if ($taskFile.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked module file is not permitted' }
 $taskRelative=$taskFile.FullName.Substring($taskSource.Length+1)
 $taskDestination=[IO.Path]::GetFullPath((Join-Path $taskTarget $taskRelative))
 if (-not $taskDestination.StartsWith($taskTarget+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'File outside test module' }
 New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskDestination)) -Force | Out-Null
 Copy-Item -LiteralPath $taskFile.FullName -Destination $taskDestination
 if ((Get-FileHash -LiteralPath $taskDestination -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $taskFile.FullName -Algorithm SHA256).Hash) { throw "Installed file differs: $taskRelative" }
}
Write-Output "Installed and verified FeifengScaleTest v0.1.0 at $taskTarget"
