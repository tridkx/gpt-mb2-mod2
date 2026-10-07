$ErrorActionPreference='Stop'
$project=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python='C:/ProgramData/anaconda3/python.exe'
$blender='D:/Blender Foundation/Blender 5.2/blender.exe'
$dll=Join-Path $project 'build/sleeve_tool/bin/SleeveTool.dll'
function Check-Step {if($LASTEXITCODE -ne 0){throw 'Direct cloth build failed; installation not performed.'}}
& $python -X utf8 (Join-Path $PSScriptRoot 'restore_sleeve_baseline.py');Check-Step
dotnet build (Join-Path $PSScriptRoot 'SleeveTool/SleeveTool.csproj') -o (Join-Path $project 'build/sleeve_tool/bin') --configfile (Join-Path $project '../../tools/AssetTool/NuGet.Config') -v quiet;Check-Step
dotnet $dll dump (Join-Path $project 'build/sleeve_baseline/tx5.tpac') (Join-Path $project 'build/sleeve_baseline/meshes.json');Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'prepare_direct_mask.py');Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'prepare_direct_cloth.py');Check-Step
dotnet $dll direct (Join-Path $project 'build/sleeve_baseline/tx5.tpac') (Join-Path $project 'build/direct_cloth/recipe.json') (Join-Path $project 'build/direct_cloth/tx5.tpac');Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'update_direct_source.py') *> (Join-Path $project 'reports/direct_source.log');Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'verify_direct_source.py') *> (Join-Path $project 'reports/direct_source_check.log');Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'verify_direct_cloth.py');Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'prepare_direct_review.py');Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'render_direct_review.py') *> (Join-Path $project 'reports/direct_review.log');Check-Step
Copy-Item -LiteralPath (Join-Path $project 'build/direct_cloth/tx5.tpac') -Destination (Join-Path $project 'module/TianxiangT5/AssetPackages/tx5.tpac') -Force
Write-Output 'Direct cloth built and checked; no game launched or installed.'
