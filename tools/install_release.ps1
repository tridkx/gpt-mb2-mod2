param(
    [Parameter(Mandatory=$true)][ValidatePattern('^v\d+\.\d+\.\d+$')][string]$Version,
    [Parameter(Mandatory=$true)][ValidatePattern('^v\d+\.\d+\.\d+$')][string]$PreviousVersion
)
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if ($workspaceRoot -ne 'D:\gpt-mb2-mod2') { throw 'Unexpected workspace' }
Set-Location -LiteralPath $workspaceRoot
$sourceModulePath = [IO.Path]::GetFullPath((Join-Path $workspaceRoot 'module\TianxiangT5'))
$installedModulePath = [IO.Path]::GetFullPath('D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord\Modules\TianxiangT5')
if ($installedModulePath -ne 'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord\Modules\TianxiangT5') { throw 'Unexpected install target' }
[xml]$descriptor = Get-Content -LiteralPath (Join-Path $sourceModulePath 'SubModule.xml') -Encoding UTF8
if ($descriptor.Module.Version.value -ne $Version) { throw 'Build version differs from requested release' }
$runningGame = Get-Process | Where-Object { $_.ProcessName -match 'Bannerlord|TaleWorlds' }
if ($runningGame) { throw 'Exit the game and launcher before installing loaded assets' }
$postureReport = Get-Content -LiteralPath 'reports\posture_validation.json' -Raw -Encoding UTF8 | ConvertFrom-Json
$assetHash = (Get-FileHash -LiteralPath 'module\TianxiangT5\AssetPackages\tx5.tpac' -Algorithm SHA256).Hash
if ($postureReport.version -ne $Version -or $postureReport.final_package_sha256 -ne $assetHash) { throw 'Package does not match posture validation' }
Copy-Item -LiteralPath 'README.md' -Destination 'module\TianxiangT5\README.txt' -Force
foreach ($kind in @('Mod','Source')) {
    $currentArchive = Join-Path $workspaceRoot ('dist\TianxiangT5_' + $kind + '.zip')
    $previousArchive = Join-Path $workspaceRoot ('dist\TianxiangT5_' + $PreviousVersion + '_' + $kind + '.zip')
    if ((Test-Path -LiteralPath $currentArchive) -and -not (Test-Path -LiteralPath $previousArchive)) {
        Copy-Item -LiteralPath $currentArchive -Destination $previousArchive
    }
}
$installedFiles = 0
foreach ($moduleFile in (Get-ChildItem -LiteralPath $sourceModulePath -Recurse -File)) {
    $relativeFile = $moduleFile.FullName.Substring($sourceModulePath.Length + 1)
    $destinationFile = [IO.Path]::GetFullPath((Join-Path $installedModulePath $relativeFile))
    if (-not $destinationFile.StartsWith($installedModulePath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Install file outside intended module' }
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destinationFile)) -Force | Out-Null
    Copy-Item -LiteralPath $moduleFile.FullName -Destination $destinationFile -Force
    if ((Get-FileHash -LiteralPath $moduleFile.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash) {
        throw ('Installed file differs: ' + $relativeFile)
    }
    $installedFiles++
}
& 'C:\ProgramData\anaconda3\python.exe' 'tools\package_delivery.py' $Version
if ($LASTEXITCODE -ne 0) { throw 'Delivery package verification failed' }
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Change validation failed' }
git add -- 'README.md' 'module/TianxiangT5/README.txt' 'module/TianxiangT5/SubModule.xml' 'module/TianxiangT5/AssetPackages/tx5.tpac' 'source/TianxiangT5_Rigged.blend' 'source/TianxiangT5_Rigged.fbx' 'tools/motion_fit.py' 'tools/rig_model.py' 'tools/verify_motion.py' 'tools/verify_posture.py' 'tools/render_motion_review.py' 'tools/package_delivery.py' 'tools/install_release.ps1' 'reports/validation.json' 'reports/posture_validation.json' 'reports/motion_validation_v1.3.0.json' 'reports/visibility_validation_materials.json' 'reports/posture_before_front.png' 'reports/posture_after_front.png' 'reports/posture_before_side.png' 'reports/posture_after_side.png' 'reports/posture_before_run_side.png' 'reports/posture_after_run_side.png'
if ($LASTEXITCODE -ne 0) { throw 'Git staging failed' }
git commit -m 'Increase arm forward angle and fill out chest-to-waist volume' -m 'Add 20 degrees to the previous 6 degree arm posture. Widen the torso by 8 percent and increase depth by 5 percent with matching garment changes. Preserve skirt anchors and cloth data; include offline dimensions, native poses and final asset checks.'
if ($LASTEXITCODE -ne 0) { throw 'Local version commit failed' }
git tag -a $Version -m 'Arm posture and torso volume revision; game testing by user'
if ($LASTEXITCODE -ne 0) { throw 'Local version tag failed' }
git status --short
git log -1 --oneline
Write-Output ('Installed ' + $Version + '; verified ' + $installedFiles + ' files; archives checked and version saved locally.')
