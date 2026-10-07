param([switch]$Preview)
$ErrorActionPreference='Stop'
$project=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python='C:/ProgramData/anaconda3/python.exe'
$blender='D:/Blender Foundation/Blender 5.2/blender.exe'
$dll=Join-Path $project 'build/sleeve_tool/bin/SleeveTool.dll'
function Check-Step { if ($LASTEXITCODE -ne 0) { throw 'Sleeve build step failed; installation was not requested by this script.' } }
& $python -X utf8 (Join-Path $PSScriptRoot 'restore_sleeve_baseline.py'); Check-Step
dotnet build (Join-Path $PSScriptRoot 'SleeveTool/SleeveTool.csproj') -o (Join-Path $project 'build/sleeve_tool/bin') --configfile (Join-Path $project '../../tools/AssetTool/NuGet.Config') -v quiet; Check-Step
dotnet $dll dump (Join-Path $project 'build/sleeve_baseline/tx5.tpac') (Join-Path $project 'build/sleeve_baseline/meshes.json'); Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'prepare_sleeves.py'); Check-Step
dotnet $dll patch (Join-Path $project 'build/sleeve_baseline/tx5.tpac') (Join-Path $project 'build/sleeve_recipe.json') (Join-Path $project 'module/TianxiangT5/AssetPackages/tx5.tpac'); Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'update_sleeve_source.py') *> (Join-Path $project 'reports/sleeve_source.log'); Check-Step
dotnet $dll dump (Join-Path $project 'module/TianxiangT5/AssetPackages/tx5.tpac') (Join-Path $project 'build/sleeve_final.json'); Check-Step
& $python -X utf8 'C:/Users/DKX/.codex/skills/bannerlord-equipment-mod/scripts/audit_package.py' (Join-Path $project 'module/TianxiangT5/AssetPackages/tx5.tpac') --cloth-vertex-alpha *> (Join-Path $project 'reports/sleeve_asset_audit.json'); Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'verify_sleeve_source.py') *> (Join-Path $project 'reports/sleeve_source_check.log'); Check-Step
& $python -X utf8 (Join-Path $PSScriptRoot 'verify_sleeves.py'); Check-Step
if ($Preview) {
    & $python -X utf8 (Join-Path $PSScriptRoot 'preview_sleeves.py') *> (Join-Path $project 'reports/sleeve_proxy.log'); Check-Step
    & $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'render_sleeves.py') *> (Join-Path $project 'reports/sleeve_render.log'); Check-Step
}
Write-Output 'Water sleeve build and offline checks completed; no game launched or installed.'
