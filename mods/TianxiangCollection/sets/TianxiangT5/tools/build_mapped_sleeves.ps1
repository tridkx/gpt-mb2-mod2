$ErrorActionPreference='Stop'
$project=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$python='C:/ProgramData/anaconda3/python.exe'
$blender='D:/Blender Foundation/Blender 5.2/blender.exe'
$native='D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord/Modules/Native/AssetPackages'
$dll=Join-Path $project 'build/sleeve_tool/bin/SleeveTool.dll'
function Check-Step {if($LASTEXITCODE -ne 0){throw 'Mapped build failed; no installation performed.'}}
& $python (Join-Path $PSScriptRoot 'restore_sleeve_baseline.py');Check-Step
& $python (Join-Path $PSScriptRoot 'restore_mapped_baseline.py');Check-Step
dotnet build (Join-Path $PSScriptRoot 'SleeveTool/SleeveTool.csproj') -o (Join-Path $project 'build/sleeve_tool/bin') --configfile (Join-Path $project '../../../../tools/AssetTool/NuGet.Config') -v quiet;Check-Step
dotnet $dll dump (Join-Path $project 'build/sleeve_baseline/tx5.tpac') (Join-Path $project 'build/sleeve_baseline/meshes.json');Check-Step
& $python (Join-Path $PSScriptRoot 'prepare_sleeves.py');Check-Step
dotnet $dll dump (Join-Path $project 'build/mapped_baseline/tx5.tpac') (Join-Path $project 'build/sleeve_final.json');Check-Step
foreach($sample in @(@('clo_battania_dress_c','native_proxy'),@('clo_khuzait_civil_coat','native_coat'))){
    $folder=Join-Path $project ('build/cloth_format/'+$sample[1])
    dotnet $dll inspect (Join-Path $native 'meshes_shared_3.tpac') $sample[0] $folder;Check-Step
    dotnet $dll dump (Join-Path $native 'meshes_shared_3.tpac') (Join-Path $folder 'meshes.json') $sample[0];Check-Step
}
& $python (Join-Path $PSScriptRoot 'build_mapped_recipe.py');Check-Step
dotnet $dll mapped (Join-Path $project 'build/mapped_baseline/tx5.tpac') (Join-Path $project 'build/mapped/recipe.json') (Join-Path $project 'build/mapped/tx5.tpac');Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'update_mapped_source.py') *> (Join-Path $project 'reports/mapped_source.log');Check-Step
& $blender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'verify_sleeve_source.py') *> (Join-Path $project 'reports/mapped_source_check.log');Check-Step
& $python (Join-Path $PSScriptRoot 'verify_mapped_sleeves.py');Check-Step
Copy-Item -LiteralPath (Join-Path $project 'build/mapped/tx5.tpac') -Destination (Join-Path $project 'module/TianxiangT5/AssetPackages/tx5.tpac') -Force
Write-Output 'Mapped simulation built and verified; own workspace module updated; no game launched or installed.'
