param([string]$Python='C:/ProgramData/anaconda3/python.exe',[string]$Blender='D:/Blender Foundation/Blender 5.2/blender.exe')
$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$workspaceRoot=$projectRoot
while (-not (Test-Path -LiteralPath (Join-Path $workspaceRoot 'tools/AssetTool/NuGet.Config'))) {
    $parent=[IO.Directory]::GetParent($workspaceRoot)
    if ($null -eq $parent) { throw 'Workspace tools/AssetTool/NuGet.Config not found' }
    $workspaceRoot=$parent.FullName
}
Push-Location $workspaceRoot
try {
    & dotnet build "$projectRoot/tools/SleeveTool/SleeveTool.csproj" -o "$projectRoot/build/sleeve_tool/bin" --configfile tools/AssetTool/NuGet.Config -v quiet
    if($LASTEXITCODE -ne 0){throw 'Resource tool build failed'}
    & $Python -X utf8 "$PSScriptRoot/build_appearance.py"
    if($LASTEXITCODE -ne 0){throw 'Appearance package build failed'}
    foreach($step in @('edit_appearance_source','verify_appearance_source')) {
        & $Blender --background --python-exit-code 1 --python "$PSScriptRoot/$step.py" *> "$projectRoot/reports/$step.log"
        if($LASTEXITCODE -ne 0){throw "$step failed; inspect the report log"}
    }
    & $Python -X utf8 "$PSScriptRoot/verify_appearance.py"
    if($LASTEXITCODE -ne 0){throw 'Final package validation failed'}
    & $Blender --background --python-exit-code 1 --python "$PSScriptRoot/render_appearance_review.py" *> "$projectRoot/reports/appearance_render.log"
    if($LASTEXITCODE -ne 0){throw 'Preview rendering failed'}
    & $Python -X utf8 "$PSScriptRoot/compose_appearance_review.py"
    if($LASTEXITCODE -ne 0){throw 'Comparison image failed'}
    Copy-Item -LiteralPath "$projectRoot/build/no_cloth/tx5.tpac" -Destination "$projectRoot/module/TianxiangT5/AssetPackages/tx5.tpac" -Force
    $config=Get-Content -LiteralPath "$PSScriptRoot/appearance_config.json" -Raw | ConvertFrom-Json
    $descriptor="$projectRoot/module/TianxiangT5/SubModule.xml"
    $text=Get-Content -LiteralPath $descriptor -Raw -Encoding UTF8
    $text=$text -replace '<Version value="v\d+\.\d+\.\d+" />',"<Version value=`"$($config.version)`" />"
    $text=$text.Replace('天香 T5 · 衣装与布料','天香 T5 · 衣装')
    [IO.File]::WriteAllText($descriptor,$text,[Text.UTF8Encoding]::new($false))
    $moduleReadme='天香 T5 '+$config.version+'：以 v1.4.0 为基线，停用本模组布料模拟，大腿 mesh_06 改用不透明 body_D 材质，删除两侧长水袖，头部连同头发、头饰放大约20%，保留脖子接缝。离线检查通过；游戏测试由你完成。原版与历史交付包保留。'+[Environment]::NewLine
    [IO.File]::WriteAllText("$projectRoot/module/TianxiangT5/README.txt",$moduleReadme,[Text.UTF8Encoding]::new($false))
    Write-Output 'Appearance release built, verified and staged; package/install with the common release installer.'
} finally { Pop-Location }
