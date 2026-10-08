$ErrorActionPreference='Stop'
$project=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python='C:/ProgramData/anaconda3/python.exe'
$blender='D:/Blender Foundation/Blender 5.2/blender.exe'
function Check-Step {if($LASTEXITCODE -ne 0){throw 'Wind control failed; no installation performed.'}}
dotnet build (Join-Path $PSScriptRoot 'SleeveTool/SleeveTool.csproj') -o (Join-Path $project 'build/sleeve_tool/bin') --configfile (Join-Path $project '../../../../tools/AssetTool/NuGet.Config') -v quiet;Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'build_wind_control.py');Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'verify_wind_source.py') *> (Join-Path $project 'reports/wind_source_check.log');Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'verify_wind_control.py');Check-Step
Copy-Item -LiteralPath (Join-Path $project 'build/wind_control/tx5.tpac') -Destination (Join-Path $project 'module/TianxiangT5/AssetPackages/tx5.tpac') -Force
Write-Output 'Wind-only control built and checked; no game launched or installed.'
